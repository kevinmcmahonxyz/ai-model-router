"""API routes."""
import uuid
from datetime import datetime
from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from src.api.models import ChatCompletionRequest, ChatCompletionResponse, UsageInfo
from src.models.database import get_db
from src.models.schemas import User, Model, Request
from src.providers.openai_provider import OpenAIProvider
from src.services.cost_calculator import calculate_cost
from src.services.model_selector import ModelSelector

router = APIRouter()


def get_current_user(
    x_api_key: str = Header(..., alias="X-API-Key", description="API Key"),
    db: Session = Depends(get_db)
) -> User:
    """Validate API key and return user."""
    user = db.query(User).filter(User.api_key == x_api_key).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    return user


async def _send_to_provider(
    model: Model,
    messages: List[Dict[str, str]],
    request_params: Dict
) -> Dict:
    """
    Send request to appropriate provider.
    
    Args:
        model: Model database object
        messages: List of message dicts
        request_params: Additional request parameters
    
    Returns:
        Result dict from provider
    """
    # For Phase 4, we only support OpenAI
    # In Phase 2, we'll add more providers here
    if model.provider.name == "openai":
        provider = OpenAIProvider()
        return await provider.send_request(
            messages=messages,
            model=model.model_id,
            **request_params
        )
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Provider {model.provider.name} not yet implemented"
        )


@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completion(
    request: ChatCompletionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Route chat completion request with manual or cost-optimized model selection.
    
    **Modes:**
    - `manual`: Specify model explicitly (default)
    - `cost-optimized`: Automatically select cheapest model
    
    **Cost-Optimized Features:**
    - Estimates cost before sending request
    - Selects cheapest available model
    - Falls back to next cheapest if first fails
    - Respects max_cost and provider_filter constraints
    """
    
    # Validate request based on mode
    if request.mode == "manual" and not request.model:
        raise HTTPException(
            status_code=400,
            detail="model is required when mode is 'manual'"
        )
    
    # Convert messages to dict format
    messages = [msg.dict() for msg in request.messages]
    
    # Prepare request params
    request_params = {}
    if request.temperature is not None:
        request_params["temperature"] = request.temperature
    if request.max_tokens is not None:
        request_params["max_tokens"] = request.max_tokens
    
    # Extract prompt text for logging
    prompt_text = next(
        (msg["content"] for msg in reversed(messages) if msg["role"] == "user"),
        ""
    )
    
    # MANUAL MODE: User specifies model
    if request.mode == "manual":
        # Look up the model
        model = db.query(Model).filter(
            Model.model_id == request.model,
            Model.is_active == True
        ).first()
        
        if not model:
            raise HTTPException(
                status_code=400,
                detail=f"Model '{request.model}' not found or inactive"
            )
        
        # Send request
        result = await _send_to_provider(model, messages, request_params)
        
        if not result["success"]:
            # Log failed request
            request_log = Request(
                id=uuid.uuid4(),
                user_id=user.id,
                model_id=model.id,
                provider_id=model.provider_id,
                prompt_text=prompt_text,
                response_text=None,
                status="error",
                error_message=result["error"],
                latency_ms=result["latency_ms"],
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            db.add(request_log)
            db.commit()
            
            raise HTTPException(status_code=500, detail=f"Provider error: {result['error']}")
        
        models_considered = None
        selection_mode = "manual"
        estimated_cost = None
    
    # COST-OPTIMIZED MODE: Automatically select cheapest
    else:
        selector = ModelSelector(db)
        
        # Get ranked models
        ranked_models = selector.get_ranked_models(
            messages=messages,
            expected_output_tokens=request.expected_output_tokens,
            provider_filter=request.provider_filter,
            max_cost=request.max_cost
        )
        
        if not ranked_models:
            raise HTTPException(
                status_code=400,
                detail="No models available matching constraints"
            )
        
        models_considered = len(ranked_models)
        estimated_cost = ranked_models[0]["estimated_cost"]
        
        print(f"\n{'='*60}")
        print(f"🎯 COST-OPTIMIZED MODE")
        print(f"{'='*60}")
        print(f"Models evaluated: {models_considered}")
        print(f"Selected: {ranked_models[0]['display_name']} (${estimated_cost:.6f})")
        print(f"{'='*60}\n")
        
        # Try models in order (cheapest first) until one succeeds
        result = None
        model = None
        
        for model_info in ranked_models:
            # Get model from database
            model = db.query(Model).filter(
                Model.id == model_info["model_db_id"]
            ).first()
            
            print(f"→ Trying {model_info['display_name']}...")
            
            # Send request
            result = await _send_to_provider(model, messages, request_params)
            
            if result["success"]:
                print(f"✓ Success with {model_info['display_name']}")
                break
            else:
                print(f"✗ Failed with {model_info['display_name']}: {result['error']}")
                # Try next model
                continue
        
        # If all models failed
        if not result or not result["success"]:
            raise HTTPException(
                status_code=500,
                detail="All available models failed"
            )
        
        selection_mode = "cost-optimized"
    
    # Calculate actual cost
    usage = result["usage"]
    cost_info = calculate_cost(
        input_tokens=usage["input_tokens"],
        output_tokens=usage["output_tokens"],
        input_price_per_1m=model.input_price_per_1m_tokens,
        output_price_per_1m=model.output_price_per_1m_tokens
    )
    
    # Log successful request
    request_id = uuid.uuid4()
    request_log = Request(
        id=request_id,
        user_id=user.id,
        model_id=model.id,
        provider_id=model.provider_id,
        prompt_text=prompt_text,
        response_text=result["content"],
        input_tokens=usage["input_tokens"],
        output_tokens=usage["output_tokens"],
        total_tokens=usage["total_tokens"],
        input_cost_usd=cost_info["input_cost_usd"],
        output_cost_usd=cost_info["output_cost_usd"],
        total_cost_usd=cost_info["total_cost_usd"],
        latency_ms=result["latency_ms"],
        status="success",
        created_at=datetime.utcnow(),
        completed_at=datetime.utcnow()
    )
    db.add(request_log)
    db.commit()
    
    # Console output
    print(f"\n{'='*60}")
    print(f"✓ Request successful")
    print(f"Mode: {selection_mode}")
    print(f"Model: {model.model_id}")
    if estimated_cost:
        print(f"Estimated cost: ${estimated_cost:.6f}")
    print(f"Actual cost: ${cost_info['total_cost_usd']:.6f}")
    print(f"Tokens: {usage['input_tokens']} in / {usage['output_tokens']} out")
    print(f"Latency: {result['latency_ms']}ms")
    print(f"{'='*60}\n")
    
    # Return response
    return ChatCompletionResponse(
        id=str(request_id),
        model=model.model_id,
        provider=model.provider.name,
        content=result["content"],
        finish_reason=result["finish_reason"],
        usage=UsageInfo(
            prompt_tokens=usage["input_tokens"],
            completion_tokens=usage["output_tokens"],
            total_tokens=usage["total_tokens"],
            input_cost_usd=cost_info["input_cost_usd"],
            output_cost_usd=cost_info["output_cost_usd"],
            total_cost_usd=cost_info["total_cost_usd"],
            estimated_cost_usd=estimated_cost
        ),
        latency_ms=result["latency_ms"],
        created_at=datetime.utcnow().isoformat(),
        selection_mode=selection_mode,
        models_considered=models_considered
    )


@router.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "service": "ai-model-router"}