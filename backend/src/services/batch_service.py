"""Batch processing service for concurrent requests."""
import asyncio
import uuid
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from src.models.schemas import Model, Request
from src.providers.openai_provider import OpenAIProvider
from src.providers.anthropic_provider import AnthropicProvider
from src.providers.deepseek_provider import DeepSeekProvider
from src.providers.google_provider import GoogleProvider
from src.services.cost_calculator import calculate_cost
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class BatchService:
    """Handle batch processing of multiple requests concurrently."""
    
    def __init__(self, db: Session):
        self.db = db
        self.providers = {
            'openai': OpenAIProvider(),
            'anthropic': AnthropicProvider(),
            'deepseek': DeepSeekProvider(),
            'google': GoogleProvider()
        }
    
    async def _process_single_request(
        self,
        model: Model,
        messages: List[Dict[str, str]],
        request_params: Dict[str, Any],
        user_id: uuid.UUID,
        batch_id: uuid.UUID,
        request_index: int,
        request_id: str
    ) -> Dict[str, Any]:
        """
        Process a single request in the batch.
        
        Args:
            model: Model database object
            messages: List of message dicts
            request_params: Additional parameters
            user_id: User ID
            batch_id: Batch ID to link requests
            request_index: Position in batch
            request_id: User-provided or generated ID
        
        Returns:
            Dict with result information
        """
        start_time = datetime.utcnow()
        db_request_id = uuid.uuid4()
        
        try:
            # Get provider
            provider = self.providers.get(model.provider.name)
            if not provider:
                raise ValueError(f"Provider {model.provider.name} not found")
            
            # Send request
            result = await provider.send_request(
                messages=messages,
                model=model.model_id,
                **request_params
            )
            
            # Calculate metrics
            end_time = datetime.utcnow()
            latency_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Extract token usage
            usage = result.get('usage')
            if usage and isinstance(usage, dict):
                input_tokens = usage.get('input_tokens', 0)
                output_tokens = usage.get('output_tokens', 0)
                total_tokens = usage.get('total_tokens', input_tokens + output_tokens)
            else:
                input_tokens = 0
                output_tokens = 0
                total_tokens = 0
            
            # Calculate costs
            cost_info = calculate_cost(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                input_price_per_1m=model.input_price_per_1m_tokens,
                output_price_per_1m=model.output_price_per_1m_tokens
            )
            input_cost = cost_info['input_cost_usd']
            output_cost = cost_info['output_cost_usd']
            total_cost = cost_info['total_cost_usd']
            
            # Log to database
            db_request = Request(
                id=db_request_id,
                user_id=user_id,
                model_id=model.id,
                provider_id=model.provider_id,
                prompt_text=str(messages),
                response_text=result.get('content'),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                input_cost_usd=input_cost,
                output_cost_usd=output_cost,
                total_cost_usd=total_cost,
                latency_ms=latency_ms,
                status='success',
                created_at=start_time,
                completed_at=end_time
            )
            self.db.add(db_request)
            
            logger.debug(f"Batch request {request_index + 1} succeeded ({latency_ms}ms)")
            
            return {
                'id': request_id,
                'index': request_index,
                'content': result.get('content'),
                'finish_reason': result.get('finish_reason'),
                'usage': {
                    'prompt_tokens': input_tokens,
                    'completion_tokens': output_tokens,
                    'total_tokens': total_tokens,
                    'input_cost_usd': input_cost,
                    'output_cost_usd': output_cost,
                    'total_cost_usd': total_cost
                },
                'status': 'success',
                'error_message': None
            }
            
        except Exception as e:
            # Log error
            end_time = datetime.utcnow()
            latency_ms = int((end_time - start_time).total_seconds() * 1000)
            
            db_request = Request(
                id=db_request_id,
                user_id=user_id,
                model_id=model.id,
                provider_id=model.provider_id,
                prompt_text=str(messages),
                response_text=None,
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                input_cost_usd=0.0,
                output_cost_usd=0.0,
                total_cost_usd=0.0,
                latency_ms=latency_ms,
                status='error',
                error_message=str(e),
                created_at=start_time,
                completed_at=end_time
            )
            self.db.add(db_request)
            
            logger.error(f"Batch request {request_index + 1} failed: {str(e)}")
            
            return {
                'id': request_id,
                'index': request_index,
                'content': None,
                'finish_reason': None,
                'usage': {
                    'prompt_tokens': 0,
                    'completion_tokens': 0,
                    'total_tokens': 0,
                    'input_cost_usd': 0.0,
                    'output_cost_usd': 0.0,
                    'total_cost_usd': 0.0
                },
                'status': 'error',
                'error_message': str(e)
            }
    
    async def process_batch(
        self,
        user_id: uuid.UUID,
        model_id: str,
        requests: List[Dict[str, Any]],
        request_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process multiple requests concurrently.
        
        Args:
            user_id: User ID
            model_id: Model to use for all requests
            requests: List of request dicts with 'messages' and optional 'id'
            request_params: Additional parameters (temperature, max_tokens)
        
        Returns:
            Dict with batch results
        """
        batch_id = uuid.uuid4()
        start_time = datetime.utcnow()
        
        # Get model
        model = self.db.query(Model).filter(
            Model.model_id == model_id,
            Model.is_active == True
        ).first()
        
        if not model:
            raise ValueError(f"Model {model_id} not found or inactive")
        
        logger.info(
            f"Starting batch {batch_id}: {len(requests)} requests using {model.display_name}"
        )
        
        # Create tasks for all requests
        tasks = []
        for i, req in enumerate(requests):
            # Use user-provided ID or generate one
            req_id = req.get('id', str(uuid.uuid4()))
            
            task = self._process_single_request(
                model=model,
                messages=req['messages'],
                request_params=request_params,
                user_id=user_id,
                batch_id=batch_id,
                request_index=i,
                request_id=req_id
            )
            tasks.append(task)
        
        # Execute all requests concurrently
        results = await asyncio.gather(*tasks)
        
        # Calculate aggregate metrics
        end_time = datetime.utcnow()
        total_latency_ms = int((end_time - start_time).total_seconds() * 1000)
        
        successful = sum(1 for r in results if r['status'] == 'success')
        failed = sum(1 for r in results if r['status'] == 'error')
        total_cost = sum(r['usage']['total_cost_usd'] for r in results)
        
        # Commit all database changes
        self.db.commit()
        
        logger.info(
            f"Batch {batch_id} complete - "
            f"Success: {successful}/{len(requests)}, "
            f"Cost: ${total_cost:.6f}, "
            f"Time: {total_latency_ms}ms"
        )
        
        return {
            'batch_id': str(batch_id),
            'total_requests': len(requests),
            'successful': successful,
            'failed': failed,
            'results': results,
            'total_cost_usd': total_cost,
            'total_latency_ms': total_latency_ms,
            'created_at': start_time.isoformat()
        }