"""API routes."""
# Standard library imports
import uuid
from datetime import datetime
from typing import Dict

# Third-party imports
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

# Local application imports
from src.api.models import ChatCompletionRequest, ChatCompletionResponse, UsageInfo
from src.models.database import get_db, settings
from src.models.schemas import User, Model, Request, Provider
from src.providers.openai_provider import OpenAIProvider
from src.providers.anthropic_provider import AnthropicProvider
from src.services.cost_calculator import calculate_cost

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


@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completion(
    request: ChatCompletionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Route chat completion request to appropriate provider.
    
    **Phase 2 Update:**
    - Now supports multiple providers (OpenAI, Anthropic)
    - Automatically routes based on model name
    - All providers return standardized response format
    """
    
    # Look up the model in database
    model = db.query(Model).filter(
        Model.model_id == request.model,
        Model.is_active == True
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=400,
            detail=f"Model '{request.model}' not found or inactive"
        )
    
    # Get provider info
    provider_record = db.query(Provider).filter(
        Provider.id == model.provider_id
    ).first()
    
    if not provider_record or not provider_record.is_active:
        raise HTTPException(
            status_code=500,
            detail=f"Provider for model '{request.model}' is not available"
        )
    
    if provider_record.name == "openai":
        provider = OpenAIProvider(api_key=settings.openai_api_key)
    elif provider_record.name == "anthropic":
        provider = AnthropicProvider(api_key=settings.anthropic_api_key)
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Provider '{provider_record.name}' not implemented"
        )
    
    # Convert Pydantic messages to dict format
    messages = [msg.dict() for msg in request.messages]
    
    # Prepare request params
    request_params = {}
    if request.temperature is not None:
        request_params["temperature"] = request.temperature
    if request.max_tokens is not None:
        request_params["max_tokens"] = request.max_tokens
    
    # Extract prompt text for logging (just the last user message for simplicity)
    prompt_text = next(
        (msg["content"] for msg in reversed(messages) if msg["role"] == "user"),
        ""
    )
    
    # Send request to provider
    result = await provider.send_request(
        messages=messages,
        model=request.model,
        **request_params
    )
    
    # Handle error from provider
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
    
    # Calculate cost
    usage = result["usage"]
    cost_info = calculate_cost(
        input_tokens=usage["input_tokens"],
        output_tokens=usage["output_tokens"],
        input_price_per_1m=model.input_price_per_1m_tokens,
        output_price_per_1m=model.output_price_per_1m_tokens
    )
    
    # Log successful request to database
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
    
    # Print to console for visibility (learning/debugging)
    print(f"\n{'='*60}")
    print(f"✓ Request successful")
    print(f"Provider: {provider_record.name}")
    print(f"Model: {request.model}")
    print(f"Tokens: {usage['input_tokens']} in / {usage['output_tokens']} out")
    print(f"Cost: ${cost_info['total_cost_usd']:.6f}")
    print(f"Latency: {result['latency_ms']}ms")
    print(f"{'='*60}\n")
    
    # Return response
    return ChatCompletionResponse(
        id=str(request_id),
        model=result["model"],
        provider=provider_record.name,  # Now dynamic based on actual provider
        content=result["content"],
        finish_reason=result["finish_reason"],
        usage=UsageInfo(
            prompt_tokens=usage["input_tokens"],
            completion_tokens=usage["output_tokens"],
            total_tokens=usage["total_tokens"],
            input_cost_usd=cost_info["input_cost_usd"],
            output_cost_usd=cost_info["output_cost_usd"],
            total_cost_usd=cost_info["total_cost_usd"]
        ),
        latency_ms=result["latency_ms"],
        created_at=datetime.utcnow().isoformat()
    )


@router.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "service": "ai-model-router"}