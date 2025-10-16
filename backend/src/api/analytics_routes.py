"""Analytics API endpoints for dashboard."""
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.models.database import get_db
from src.models.schemas import Request, Model, Provider, User
from src.api.routes import get_current_user

router = APIRouter(prefix="/v1/analytics", tags=["analytics"])


# Response models
class ProviderStats(BaseModel):
    """Stats for a single provider."""
    provider: str
    requests: int
    cost_usd: float


class ModelStats(BaseModel):
    """Stats for a single model."""
    model: str
    requests: int
    cost_usd: float


class DailyStats(BaseModel):
    """Stats for a single day."""
    date: str
    requests: int
    cost_usd: float


class UsageResponse(BaseModel):
    """Overall usage statistics."""
    total_requests: int
    total_cost_usd: float
    avg_latency_ms: int
    success_rate: float
    by_provider: List[ProviderStats]
    by_model: List[ModelStats]
    daily_stats: List[DailyStats]


class RequestSummary(BaseModel):
    """Summary of a single request for list view."""
    id: str
    created_at: str
    model: str
    provider: str
    prompt_preview: str
    input_tokens: int
    output_tokens: int
    total_cost_usd: float
    latency_ms: int
    status: str


class RequestListResponse(BaseModel):
    """Paginated list of requests."""
    requests: List[RequestSummary]
    total: int
    page: int
    per_page: int
    total_pages: int


class RequestDetail(BaseModel):
    """Full detail of a single request."""
    id: str
    created_at: str
    completed_at: Optional[str]
    model: str
    provider: str
    prompt_text: str
    response_text: Optional[str]
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    total_tokens: Optional[int]
    input_cost_usd: Optional[float]
    output_cost_usd: Optional[float]
    total_cost_usd: Optional[float]
    latency_ms: Optional[int]
    status: str
    error_message: Optional[str]


class ModelInfo(BaseModel):
    """Information about an available model."""
    id: int
    model_id: str
    display_name: str
    provider: str
    input_price_per_1m_tokens: float
    output_price_per_1m_tokens: float
    context_window: Optional[int]
    is_active: bool


@router.get("/usage", response_model=UsageResponse)
async def get_usage_stats(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get aggregate usage statistics.
    
    **Query parameters:**
    - days: Number of days to look back (default 30, max 365)
    
    **Returns:**
    - Total requests, cost, latency, success rate
    - Breakdown by provider
    - Breakdown by model
    - Daily time series data
    """
    # Calculate date threshold
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get all requests for this user in date range
    requests = db.query(Request).filter(
        and_(
            Request.user_id == user.id,
            Request.created_at >= start_date
        )
    ).all()
    
    if not requests:
        return UsageResponse(
            total_requests=0,
            total_cost_usd=0.0,
            avg_latency_ms=0,
            success_rate=0.0,
            by_provider=[],
            by_model=[],
            daily_stats=[]
        )
    
    # Calculate total stats
    total_requests = len(requests)
    total_cost = sum(r.total_cost_usd or 0 for r in requests)
    avg_latency = int(sum(r.latency_ms or 0 for r in requests) / total_requests)
    success_count = sum(1 for r in requests if r.status == "success")
    success_rate = round(success_count / total_requests, 3)
    
    # Group by provider
    provider_map = {}
    for req in requests:
        provider_name = db.query(Provider.name).filter(Provider.id == req.provider_id).scalar()
        if provider_name not in provider_map:
            provider_map[provider_name] = {"requests": 0, "cost": 0.0}
        provider_map[provider_name]["requests"] += 1
        provider_map[provider_name]["cost"] += req.total_cost_usd or 0
    
    by_provider = [
        ProviderStats(
            provider=name,
            requests=stats["requests"],
            cost_usd=round(stats["cost"], 6)
        )
        for name, stats in provider_map.items()
    ]
    
    # Group by model
    model_map = {}
    for req in requests:
        model_id = db.query(Model.model_id).filter(Model.id == req.model_id).scalar()
        if model_id not in model_map:
            model_map[model_id] = {"requests": 0, "cost": 0.0}
        model_map[model_id]["requests"] += 1
        model_map[model_id]["cost"] += req.total_cost_usd or 0
    
    by_model = [
        ModelStats(
            model=model_id,
            requests=stats["requests"],
            cost_usd=round(stats["cost"], 6)
        )
        for model_id, stats in sorted(model_map.items(), key=lambda x: x[1]["cost"], reverse=True)
    ]
    
    # Group by day
    daily_map = {}
    for req in requests:
        date_str = req.created_at.date().isoformat()
        if date_str not in daily_map:
            daily_map[date_str] = {"requests": 0, "cost": 0.0}
        daily_map[date_str]["requests"] += 1
        daily_map[date_str]["cost"] += req.total_cost_usd or 0
    
    daily_stats = [
        DailyStats(
            date=date_str,
            requests=stats["requests"],
            cost_usd=round(stats["cost"], 6)
        )
        for date_str, stats in sorted(daily_map.items())
    ]
    
    return UsageResponse(
        total_requests=total_requests,
        total_cost_usd=round(total_cost, 6),
        avg_latency_ms=avg_latency,
        success_rate=success_rate,
        by_provider=by_provider,
        by_model=by_model,
        daily_stats=daily_stats
    )


@router.get("/requests", response_model=RequestListResponse)
async def get_requests(
    page: int = Query(default=1, ge=1, description="Page number"),
    per_page: int = Query(default=20, ge=1, le=100, description="Items per page"),
    model: Optional[str] = Query(default=None, description="Filter by model ID"),
    status: Optional[str] = Query(default=None, description="Filter by status (success/error)"),
    search: Optional[str] = Query(default=None, description="Search in prompt text"),
    start_date: Optional[datetime] = Query(default=None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(default=None, description="Filter by end date"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of requests with filtering.
    
    **Query parameters:**
    - page: Page number (starts at 1)
    - per_page: Items per page (default 20, max 100)
    - model: Filter by model ID (e.g., 'gpt-4o-mini')
    - status: Filter by status ('success' or 'error')
    - search: Search text in prompt
    - start_date: Only requests after this date (ISO format)
    - end_date: Only requests before this date (ISO format)
    
    **Returns:**
    - List of request summaries
    - Pagination metadata
    """
    # Build query
    query = db.query(Request).filter(Request.user_id == user.id)
    
    # Apply filters
    if model:
        model_obj = db.query(Model).filter(Model.model_id == model).first()
        if model_obj:
            query = query.filter(Request.model_id == model_obj.id)
    
    if status:
        query = query.filter(Request.status == status)
    
    if search:
        query = query.filter(Request.prompt_text.ilike(f"%{search}%"))
    
    if start_date:
        query = query.filter(Request.created_at >= start_date)
    
    if end_date:
        query = query.filter(Request.created_at <= end_date)
    
    # Get total count
    total = query.count()
    
    # Calculate pagination
    total_pages = (total + per_page - 1) // per_page  # Ceiling division
    offset = (page - 1) * per_page
    
    # Get page of results
    requests = query.order_by(Request.created_at.desc()).offset(offset).limit(per_page).all()
    
    # Build response
    request_summaries = []
    for req in requests:
        # Get model and provider names
        model_obj = db.query(Model).filter(Model.id == req.model_id).first()
        provider_obj = db.query(Provider).filter(Provider.id == req.provider_id).first()
        
        # Truncate prompt for preview
        prompt_preview = req.prompt_text[:50] + "..." if len(req.prompt_text) > 50 else req.prompt_text
        
        request_summaries.append(RequestSummary(
            id=str(req.id),
            created_at=req.created_at.isoformat(),
            model=model_obj.model_id if model_obj else "unknown",
            provider=provider_obj.name if provider_obj else "unknown",
            prompt_preview=prompt_preview,
            input_tokens=req.input_tokens or 0,
            output_tokens=req.output_tokens or 0,
            total_cost_usd=req.total_cost_usd or 0.0,
            latency_ms=req.latency_ms or 0,
            status=req.status
        ))
    
    return RequestListResponse(
        requests=request_summaries,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.get("/requests/{request_id}", response_model=RequestDetail)
async def get_request_detail(
    request_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get full details of a single request.
    
    **Path parameters:**
    - request_id: UUID of the request
    
    **Returns:**
    - Complete request data including full prompt and response
    """
    # Find request
    req = db.query(Request).filter(
        and_(
            Request.id == request_id,
            Request.user_id == user.id
        )
    ).first()
    
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Get model and provider info
    model_obj = db.query(Model).filter(Model.id == req.model_id).first()
    provider_obj = db.query(Provider).filter(Provider.id == req.provider_id).first()
    
    return RequestDetail(
        id=str(req.id),
        created_at=req.created_at.isoformat(),
        completed_at=req.completed_at.isoformat() if req.completed_at else None,
        model=model_obj.model_id if model_obj else "unknown",
        provider=provider_obj.name if provider_obj else "unknown",
        prompt_text=req.prompt_text,
        response_text=req.response_text,
        input_tokens=req.input_tokens,
        output_tokens=req.output_tokens,
        total_tokens=req.total_tokens,
        input_cost_usd=req.input_cost_usd,
        output_cost_usd=req.output_cost_usd,
        total_cost_usd=req.total_cost_usd,
        latency_ms=req.latency_ms,
        status=req.status,
        error_message=req.error_message
    )


@router.get("/models", response_model=List[ModelInfo])
async def get_available_models(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of all available models with pricing.
    
    **Returns:**
    - List of all models with their configuration
    """
    models = db.query(Model).join(Provider).filter(Model.is_active == True).all()
    
    result = []
    for model in models:
        result.append(ModelInfo(
            id=model.id,
            model_id=model.model_id,
            display_name=model.display_name or model.model_id,
            provider=model.provider.name,
            input_price_per_1m_tokens=model.input_price_per_1m_tokens,
            output_price_per_1m_tokens=model.output_price_per_1m_tokens,
            context_window=model.context_window,
            is_active=model.is_active
        ))
    
    return result