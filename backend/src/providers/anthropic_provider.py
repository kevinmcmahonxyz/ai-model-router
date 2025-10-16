"""Anthropic provider implementation."""
import time
from typing import List, Dict, Any
from anthropic import Anthropic

from src.providers.base_provider import LLMProvider


class AnthropicProvider(LLMProvider):
    """Handle requests to Anthropic API."""
    
    def __init__(self, api_key: str):
        """Initialize Anthropic provider."""
        super().__init__(api_key)
        self.client = Anthropic(api_key=api_key)
        self.base_url = "https://api.anthropic.com/v1"
    
    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "anthropic"
    
    async def send_request(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send chat completion request to Anthropic.
        
        Anthropic API differences from OpenAI:
        - System messages must be passed separately (not in messages array)
        - Uses 'max_tokens' (required parameter)
        - Different response structure
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model ID (e.g., 'claude-sonnet-4-20250514')
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
        
        Returns:
            Standardized dict with response data and metadata
        """
        start_time = time.time()
        
        try:
            # Anthropic separates system messages from the messages array
            system_message = None
            anthropic_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    anthropic_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            # Anthropic requires max_tokens (set default if not provided)
            if "max_tokens" not in kwargs:
                kwargs["max_tokens"] = 4096
            
            # Build request parameters
            request_params = {
                "model": model,
                "messages": anthropic_messages,
                **kwargs
            }
            
            # Add system message if present
            if system_message:
                request_params["system"] = system_message
            
            # Call Anthropic API (synchronous - we'll make it async later)
            response = self.client.messages.create(**request_params)
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Extract response data
            # Anthropic returns content as a list of content blocks
            content_text = ""
            if response.content:
                # Get text from first content block (usually only one for text)
                content_text = response.content[0].text
            
            return {
                "success": True,
                "content": content_text,
                "finish_reason": response.stop_reason,  # 'end_turn', 'max_tokens', etc.
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
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
        Count tokens in text using Anthropic's token counting API.
        
        Note: Anthropic provides a count_tokens API, but for simplicity
        we use a rough estimation (1 token ≈ 4 characters).
        
        For production, you'd want to use the actual API:
        self.client.count_tokens(text=text)
        
        Args:
            text: Text to count tokens for
            model: Model name (not used for estimation)
        
        Returns:
            Estimated number of tokens
        """
        # Rough estimation: 1 token ≈ 4 characters
        # This is less accurate than OpenAI's tiktoken but works for estimation
        return len(text) // 4
    
    def count_messages_tokens(
        self,
        messages: List[Dict[str, str]],
        model: str
    ) -> int:
        """
        Count tokens for a list of messages.
        
        Anthropic has different overhead than OpenAI, but for Phase 2
        we'll use simple estimation.
        
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
        
        # Add small overhead for message formatting
        # Anthropic's format is simpler than OpenAI's
        total_tokens += len(messages) * 4
        
        return total_tokens