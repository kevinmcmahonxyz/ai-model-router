"""OpenAI provider implementation."""
import time
from typing import List, Dict, Any
from openai import OpenAI
import tiktoken

from src.models.database import settings


class OpenAIProvider:
    """Handle requests to OpenAI API."""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.base_url = "https://api.openai.com/v1"
    
    async def send_request(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send chat completion request to OpenAI.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model ID (e.g., 'gpt-4o-mini')
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
        
        Returns:
            Dict with response data and metadata
        """
        start_time = time.time()
        
        try:
            # Call OpenAI API
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
                    "error": "No choices returned from OpenAI API"
                }
            
            # Extract response data
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
                    "error": "No usage data returned from OpenAI API"
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
    
    def count_tokens(self, text: str, model: str) -> int:
        """
        Count tokens in text using tiktoken.
        
        Args:
            text: Text to count tokens for
            model: Model name (determines encoding)
        
        Returns:
            Number of tokens
        """
        try:
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except Exception:
            # Fallback to cl100k_base (used by gpt-4, gpt-3.5-turbo)
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
    
    def count_messages_tokens(self, messages: List[Dict[str, str]], model: str) -> int:
        """
        Count tokens for a list of messages.
        Includes overhead for message formatting.
        
        Args:
            messages: List of message dicts
            model: Model name
        
        Returns:
            Total token count
        """
        try:
            encoding = tiktoken.encoding_for_model(model)
        except Exception:
            encoding = tiktoken.get_encoding("cl100k_base")
        
        tokens_per_message = 3  # Every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = 1  # If there's a name, the role is omitted
        
        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":
                    num_tokens += tokens_per_name
        
        num_tokens += 3  # Every reply is primed with <|start|>assistant<|message|>
        
        return num_tokens