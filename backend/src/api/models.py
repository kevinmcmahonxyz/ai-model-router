"""Pydantic models for API requests and responses."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Message(BaseModel):
    """Chat message."""
    role: str = Field(..., description="Role: 'system', 'user', or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatCompletionRequest(BaseModel):
    """Request body for chat completion."""
    messages: List[Message] = Field(..., description="List of messages")
    model: str = Field(..., description="Model ID (e.g., 'gpt-4o-mini')")
    temperature: Optional[float] = Field(default=0.7, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=None, gt=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "What is the capital of France?"}
                ],
                "model": "gpt-4o-mini",
                "temperature": 0.7
            }
        }


class UsageInfo(BaseModel):
    """Token usage information."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    input_cost_usd: float
    output_cost_usd: float
    total_cost_usd: float


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