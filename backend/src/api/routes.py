"""API routes."""
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from src.api.models import ChatCompletionRequest, ChatCompletionResponse, UsageInfo
from src.models.database import get_db
from src.models.schemas import User, Model, Request
from src.providers.openai_provider import OpenAIProvider
from src.services.cost_calculator import calculate_cost
from src.services.model_selector import ModelSelector
from src.services.budget_service import BudgetService
from src.api.models import ComparisonRequest, ComparisonResponse
from src.services.comparison_service import ComparisonService

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
    from src.providers.anthropic_provider import AnthropicProvider
    from src.providers.deepseek_provider import DeepSeekProvider
    from src.providers.google_provider import GoogleProvider
    
    # Route to correct provider
    if model.provider.name == "openai":
        provider = OpenAIProvider()
    elif model.provider.name == "anthropic":
        provider = AnthropicProvider()
    elif model.provider.name == "deepseek":
        provider = DeepSeekProvider()
    elif model.provider.name == "google":
        provider = GoogleProvider()
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Provider {model.provider.name} not supported"
        )
    
    return await provider.send_request(
        messages=messages,
        model=model.model_id,
        **request_params
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

    # Budget checking for cost-optimized mode
    budget_service = BudgetService(db)
    
    if request.mode == "cost-optimized":
        selector = ModelSelector(db)
        cheapest = selector.get_cheapest_model(
            messages=messages,
            expected_output_tokens=request.expected_output_tokens,
            provider_filter=request.provider_filter
        )
        
        if cheapest:
            estimated_cost = cheapest["estimated_cost"]
            budget_check = budget_service.check_budget(user.id, estimated_cost)
            
            if not budget_check["approved"]:
                raise HTTPException(
                    status_code=402,  # Payment Required
                    detail=budget_check
                )
    
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
    
    # Update user's total spending
    budget_service.update_spending(user.id, cost_info["total_cost_usd"])

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

@router.post("/v1/chat/compare", response_model=ComparisonResponse)
async def compare_models(
    request: ComparisonRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    A/B test multiple models with the same prompt.
    
    Send the same prompt to multiple models concurrently and compare
    their responses, costs, and latencies.
    
    All requests are linked together via a comparison_id for analysis.
    """
    if not request.models or len(request.models) < 2:
        raise HTTPException(
            status_code=400,
            detail="Must specify at least 2 models for comparison"
        )
    
    if len(request.models) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 models per comparison"
        )
    
    # Build request parameters
    request_params = {}
    if request.temperature is not None:
        request_params['temperature'] = request.temperature
    if request.max_tokens is not None:
        request_params['max_tokens'] = request.max_tokens
    if request.top_p is not None:
        request_params['top_p'] = request.top_p
    
    # Execute comparison
    comparison_service = ComparisonService(db)
    result = await comparison_service.compare_models(
        user_id=user.id,
        messages=request.messages,
        model_ids=request.models,
        request_params=request_params
    )
    
    return result

@router.get("/v1/budget")
async def get_budget(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current budget and spending information."""
    budget_service = BudgetService(db)
    spending_info = budget_service.get_user_spending(user.id)
    
    return {
        "user_id": str(user.id),
        "spending": spending_info
    }


@router.put("/v1/budget/limit")
async def set_budget_limit(
    limit_usd: Optional[float] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Set spending limit for the user.
    
    Set to null for unlimited budget.
    """
    if limit_usd is not None and limit_usd < 0:
        raise HTTPException(
            status_code=400,
            detail="Spending limit must be positive or null"
        )
    
    budget_service = BudgetService(db)
    budget_service.set_spending_limit(user.id, limit_usd)
    
    return {
        "message": "Spending limit updated",
        "spending_limit_usd": limit_usd
    }


@router.post("/v1/budget/reset")
async def reset_budget(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reset spending counter to zero."""
    budget_service = BudgetService(db)
    budget_service.reset_spending(user.id)
    
    return {
        "message": "Spending counter reset to zero",
        "total_spent_usd": 0.0
    }

@router.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "service": "ai-model-router"}