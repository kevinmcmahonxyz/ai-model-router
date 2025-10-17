"""Anthropic provider implementation."""
import time
from typing import List, Dict, Any
from anthropic import Anthropic

from src.models.database import settings


class AnthropicProvider:
    """Handle requests to Anthropic API."""
    
    def __init__(self):
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.base_url = "https://api.anthropic.com"
    
    async def send_request(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send chat completion request to Anthropic.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model ID (e.g., 'claude-3-5-haiku-20241022')
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
        
        Returns:
            Dict with response data and metadata
        """
        start_time = time.time()
        
        try:
            # Convert messages to Anthropic format
            anthropic_messages = []
            system_message = None
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    anthropic_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            # Build request parameters
            request_params = {
                "model": model,
                "messages": anthropic_messages,
                "max_tokens": kwargs.get("max_tokens", 1024),
            }
            
            if system_message:
                request_params["system"] = system_message
            if "temperature" in kwargs:
                request_params["temperature"] = kwargs["temperature"]
            
            # Call Anthropic API
            response = self.client.messages.create(**request_params)
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Safety checks
            if not hasattr(response, 'content') or not response.content:
                return {
                    "success": False,
                    "content": None,
                    "finish_reason": None,
                    "usage": None,
                    "latency_ms": latency_ms,
                    "model": model,
                    "error": "No content returned from Anthropic API"
                }
            
            if len(response.content) == 0:
                return {
                    "success": False,
                    "content": None,
                    "finish_reason": None,
                    "usage": None,
                    "latency_ms": latency_ms,
                    "model": model,
                    "error": "Empty content array from Anthropic API"
                }
            
            # Extract content
            content_block = response.content[0]
            content = content_block.text if hasattr(content_block, 'text') else str(content_block)
            
            # Safety check for usage
            if not hasattr(response, 'usage') or response.usage is None:
                return {
                    "success": False,
                    "content": content,
                    "finish_reason": response.stop_reason if hasattr(response, 'stop_reason') else None,
                    "usage": None,
                    "latency_ms": latency_ms,
                    "model": model,
                    "error": "No usage data returned from Anthropic API"
                }
            
            return {
                "success": True,
                "content": content,
                "finish_reason": response.stop_reason,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                },
                "latency_ms": latency_ms,
                "model": model,
                "error": None
            }
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "success": False,
                "content": None,
                "finish_reason": None,
                "usage": None,
                "latency_ms": latency_ms,
                "model": model,
                "error": str(e)
            }
    
    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for Anthropic models.
        Uses rough approximation of 4 characters per token.
        
        Args:
            text: Text to count tokens for
        
        Returns:
            Estimated number of tokens
        """
        return len(text) // 4