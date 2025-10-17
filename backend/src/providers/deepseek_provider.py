"""DeepSeek provider implementation."""
import time
from typing import List, Dict, Any
from openai import OpenAI

from src.models.database import settings


class DeepSeekProvider:
    """Handle requests to DeepSeek API."""
    
    def __init__(self):
        # DeepSeek uses OpenAI-compatible API
        self.client = OpenAI(
            api_key=settings.deepseek_api_key,
            base_url="https://api.deepseek.com"
        )
        self.base_url = "https://api.deepseek.com"
    
    async def send_request(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send chat completion request to DeepSeek.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model ID (e.g., 'deepseek-chat')
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
        
        Returns:
            Dict with response data and metadata
        """
        start_time = time.time()
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Safety check: ensure choices exist
            if not response.choices or len(response.choices) == 0:
                return {
                    "success": False,
                    "content": None,
                    "finish_reason": None,
                    "usage": None,
                    "latency_ms": latency_ms,
                    "model": model,
                    "error": "No choices returned from DeepSeek API"
                }
            
            choice = response.choices[0]
            
            # Safety check: ensure usage exists
            if not hasattr(response, 'usage') or response.usage is None:
                return {
                    "success": False,
                    "content": choice.message.content,
                    "finish_reason": choice.finish_reason,
                    "usage": None,
                    "latency_ms": latency_ms,
                    "model": model,
                    "error": "No usage data returned from DeepSeek API"
                }
            
            usage = response.usage
            
            return {
                "success": True,
                "content": choice.message.content,
                "finish_reason": choice.finish_reason,
                "usage": {
                    "input_tokens": usage.prompt_tokens,
                    "output_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens
                },
                "latency_ms": latency_ms,
                "model": response.model,
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
        Estimate token count for DeepSeek models.
        Uses rough approximation of 4 characters per token.
        
        Args:
            text: Text to count tokens for
        
        Returns:
            Estimated number of tokens
        """
        return len(text) // 4