"""DeepSeek provider implementation."""
import time
from typing import List, Dict, Any
import httpx

from src.providers.base_provider import LLMProvider


class DeepSeekProvider(LLMProvider):
    """
    Handle requests to DeepSeek API.
    
    DeepSeek uses an OpenAI-compatible API format, making integration
    straightforward. The API is significantly cheaper than other providers.
    """
    
    def __init__(self, api_key: str):
        """Initialize DeepSeek provider."""
        super().__init__(api_key)
        self.base_url = "https://api.deepseek.com/v1"
    
    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "deepseek"
    
    async def send_request(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send chat completion request to DeepSeek.
        
        DeepSeek API is OpenAI-compatible, so the request/response
        format is very similar to OpenAI.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model ID (e.g., 'deepseek-chat')
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
        
        Returns:
            Standardized dict with response data and metadata
        """
        start_time = time.time()
        
        try:
            # Prepare request payload (OpenAI-compatible format)
            payload = {
                "model": model,
                "messages": messages,
                **kwargs
            }
            
            # Make HTTP request to DeepSeek API
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Extract response data (OpenAI-compatible format)
            choice = data["choices"][0]
            usage = data["usage"]
            
            return {
                "success": True,
                "content": choice["message"]["content"],
                "finish_reason": choice["finish_reason"],
                "usage": {
                    "input_tokens": usage["prompt_tokens"],
                    "output_tokens": usage["completion_tokens"],
                    "total_tokens": usage["total_tokens"]
                },
                "latency_ms": latency_ms,
                "model": data["model"],
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
    
    def count_tokens(self, text: str, model: str) -> int:
        """
        Count tokens in text.
        
        DeepSeek doesn't provide a tokenizer library, so we use
        rough estimation: 1 token ≈ 4 characters (similar to OpenAI).
        
        Args:
            text: Text to count tokens for
            model: Model name (not used for estimation)
        
        Returns:
            Estimated number of tokens
        """
        # Rough estimation: 1 token ≈ 4 characters
        return len(text) // 4
    
    def count_messages_tokens(
        self,
        messages: List[Dict[str, str]],
        model: str
    ) -> int:
        """
        Count tokens for a list of messages.
        
        Args:
            messages: List of message dicts
            model: Model name
        
        Returns:
            Total estimated token count
        """
        total_tokens = 0
        
        # Count tokens in each message
        for message in messages:
            content = message.get("content", "")
            total_tokens += self.count_tokens(content, model)
        
        # Add small overhead for message formatting (similar to OpenAI)
        total_tokens += len(messages) * 3
        
        return total_tokens