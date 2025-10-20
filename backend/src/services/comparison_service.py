"""Service for handling A/B comparisons across multiple models."""
import asyncio
import uuid
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from src.models.schemas import Comparison, Request, Model
from src.providers.openai_provider import OpenAIProvider
from src.providers.anthropic_provider import AnthropicProvider
from src.providers.deepseek_provider import DeepSeekProvider
from src.providers.google_provider import GoogleProvider
from src.services.cost_calculator import calculate_cost
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ComparisonService:
    """Handle A/B comparison requests across multiple models."""
    
    def __init__(self, db: Session):
        self.db = db
        self.providers = {
            'openai': OpenAIProvider(),
            'anthropic': AnthropicProvider(),
            'deepseek': DeepSeekProvider(),
            'google': GoogleProvider()
        }
    
    async def _send_to_model(
        self,
        model: Model,
        messages: List[Dict[str, str]],
        request_params: Dict[str, Any],
        user_id: uuid.UUID,
        comparison_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Send request to a single model and log the result.
        
        Args:
            model: Model database object
            messages: List of message dicts
            request_params: Additional parameters
            user_id: User ID
            comparison_id: Comparison ID to link this request
        
        Returns:
            Dict with result information
        """
        request_id = uuid.uuid4()
        start_time = datetime.utcnow()
        
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
            
            # Extract token usage - providers return input_tokens/output_tokens
            usage = result.get('usage')
            if usage and isinstance(usage, dict):
                input_tokens = usage.get('input_tokens', 0)
                output_tokens = usage.get('output_tokens', 0)
                total_tokens = usage.get('total_tokens', input_tokens + output_tokens)
            else:
                # No usage data available
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
                id=request_id,
                user_id=user_id,
                model_id=model.id,
                provider_id=model.provider_id,
                comparison_id=comparison_id,
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
            
            logger.info(f"Comparison: {model.model_id} succeeded in {latency_ms}ms, cost ${total_cost:.6f}")
            
            return {
                'model': model.model_id,
                'provider': model.provider.name,
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
                'latency_ms': latency_ms,
                'status': 'success',
                'error_message': None
            }
            
        except Exception as e:
            # Log error
            end_time = datetime.utcnow()
            latency_ms = int((end_time - start_time).total_seconds() * 1000)
            
            db_request = Request(
                id=request_id,
                user_id=user_id,
                model_id=model.id,
                provider_id=model.provider_id,
                comparison_id=comparison_id,
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
            
            logger.error(f"Comparison: {model.model_id} failed - {str(e)}")
            
            return {
                'model': model.model_id,
                'provider': model.provider.name,
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
                'latency_ms': latency_ms,
                'status': 'error',
                'error_message': str(e)
            }
    
    async def compare_models(
        self,
        user_id: uuid.UUID,
        messages: List[Dict[str, str]],
        model_ids: List[str],
        request_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send the same prompt to multiple models concurrently.
        
        Args:
            user_id: User ID
            messages: List of message dicts
            model_ids: List of model IDs to compare
            request_params: Additional parameters
        
        Returns:
            Dict with comparison results
        """
        # Create comparison record
        comparison_id = uuid.uuid4()
        prompt_text = str(messages)
        
        comparison = Comparison(
            id=comparison_id,
            user_id=user_id,
            prompt_text=prompt_text,
            models_used=model_ids,
            total_cost_usd=0.0,
            created_at=datetime.utcnow()
        )
        self.db.add(comparison)
        self.db.flush()  # Get the ID without committing
        
        # Get model objects
        models = self.db.query(Model).filter(
            Model.model_id.in_(model_ids),
            Model.is_active == True
        ).all()
        
        if len(models) != len(model_ids):
            found_models = {m.model_id for m in models}
            missing = set(model_ids) - found_models
            raise ValueError(f"Models not found or inactive: {missing}")
        
        logger.info(f"Starting comparison {comparison_id} with {len(models)} models")
        
        # Send requests concurrently
        tasks = [
            self._send_to_model(model, messages, request_params, user_id, comparison_id)
            for model in models
        ]
        results = await asyncio.gather(*tasks)
        
        # Calculate total cost from all results
        total_cost = 0.0
        for r in results:
            cost = r['usage']['total_cost_usd']
            if cost is not None:
                total_cost += float(cost)
        
        comparison.total_cost_usd = total_cost
        
        # Commit everything
        self.db.commit()
        
        logger.info(
            f"Comparison {comparison_id} complete - "
            f"Total cost: ${total_cost:.6f}"
        )
        
        return {
            'comparison_id': str(comparison_id),
            'results': results,
            'total_cost_usd': total_cost,
            'created_at': comparison.created_at.isoformat()
        }