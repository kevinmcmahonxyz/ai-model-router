"""Pydantic models for API requests and responses."""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class Message(BaseModel):
    """Chat message."""
    role: str = Field(..., description="Role: 'system', 'user', or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatCompletionRequest(BaseModel):
    """Request body for chat completion."""
    messages: List[Message] = Field(..., description="List of messages")
    model: Optional[str] = Field(
        default=None,
        description="Model ID (e.g., 'gpt-4o-mini'). Required if mode is 'manual' or not specified."
    )
    mode: Optional[Literal["manual", "cost-optimized"]] = Field(
        default="manual",
        description="Selection mode: 'manual' (specify model) or 'cost-optimized' (auto-select cheapest)"
    )
    expected_output_tokens: Optional[int] = Field(
        default=500,
        gt=0,
        description="Expected response length in tokens (used for cost estimation in cost-optimized mode)"
    )
    max_cost: Optional[float] = Field(
        default=None,
        gt=0,
        description="Maximum cost in USD (only for cost-optimized mode)"
    )
    provider_filter: Optional[List[str]] = Field(
        default=None,
        description="Limit to specific providers (e.g., ['openai', 'anthropic'])"
    )
    temperature: Optional[float] = Field(default=0.7, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=None, gt=0)
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "messages": [
                        {"role": "user", "content": "What is the capital of France?"}
                    ],
                    "model": "gpt-4o-mini",
                    "mode": "manual"
                },
                {
                    "messages": [
                        {"role": "user", "content": "Explain quantum computing."}
                    ],
                    "mode": "cost-optimized",
                    "expected_output_tokens": 300,
                    "max_cost": 0.01
                }
            ]
        }


class UsageInfo(BaseModel):
    """Token usage information."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    input_cost_usd: float
    output_cost_usd: float
    total_cost_usd: float
    estimated_cost_usd: Optional[float] = None  # For cost-optimized mode


class ChatCompletionResponse(BaseModel):
    """Response from chat completion."""
    id: str
    model: str
    provider: str
    content: str
    finish_reason: str
    usage: UsageInfo
    latency_ms: int
    created_at: str
    selection_mode: Optional[str] = None  # Track how model was selected
    models_considered: Optional[int] = None  # How many models were evaluated