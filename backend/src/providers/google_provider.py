"""Google Gemini provider implementation."""
import time
from typing import List, Dict, Any
import google.generativeai as genai

from src.providers.base_provider import LLMProvider


class GoogleProvider(LLMProvider):
    """Handle requests to Google Gemini API."""
    
    def __init__(self, api_key: str):
        """Initialize Google Gemini provider."""
        super().__init__(api_key)
        genai.configure(api_key=api_key)
        self.base_url = "https://generativelanguage.googleapis.com"
    
    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "google"
    
    async def send_request(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send chat completion request to Google Gemini.
        
        Google's API structure is different from OpenAI:
        - Separates system instructions from chat history
        - Uses 'user' and 'model' roles (not 'assistant')
        - Different response structure
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model ID (e.g., 'gemini-2.0-flash')
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
        
        Returns:
            Standardized dict with response data and metadata
        """
        start_time = time.time()
        
        try:
            # Extract system message if present
            system_instruction = None
            chat_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_instruction = msg["content"]
                else:
                    # Google uses 'user' and 'model' roles
                    role = "user" if msg["role"] == "user" else "model"
                    chat_messages.append({
                        "role": role,
                        "parts": [msg["content"]]
                    })
            
            # Create model instance
            generation_config = {}
            if "temperature" in kwargs:
                generation_config["temperature"] = kwargs["temperature"]
            if "max_tokens" in kwargs:
                generation_config["max_output_tokens"] = kwargs["max_tokens"]
            
            model_instance = genai.GenerativeModel(
                model_name=model,
                system_instruction=system_instruction,
                generation_config=generation_config if generation_config else None
            )
            
            # Generate response
            # For now, we'll use the synchronous method
            # (Google's SDK doesn't have great async support yet)
            response = model_instance.generate_content(chat_messages)
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Extract response data
            content = response.text if response.text else ""
            
            # Get usage metadata
            usage_metadata = response.usage_metadata
            input_tokens = usage_metadata.prompt_token_count
            output_tokens = usage_metadata.candidates_token_count
            
            return {
                "success": True,
                "content": content,
                "finish_reason": response.candidates[0].finish_reason.name if response.candidates else "STOP",
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens
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
    
    def count_tokens(self, text: str, model: str) -> int:
        """
        Count tokens in text using Google's tokenizer.
        
        Args:
            text: Text to count tokens for
            model: Model name
        
        Returns:
            Number of tokens
        """
        try:
            model_instance = genai.GenerativeModel(model_name=model)
            result = model_instance.count_tokens(text)
            return result.total_tokens
        except Exception:
            # Fallback to estimation: 1 token ≈ 4 characters
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
            Total token count
        """
        total_tokens = 0
        
        for message in messages:
            content = message.get("content", "")
            total_tokens += self.count_tokens(content, model)
        
        # Add small overhead for message formatting
        total_tokens += len(messages) * 2
        
        return total_tokens