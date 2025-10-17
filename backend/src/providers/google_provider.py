"""Google Gemini provider implementation."""
import time
from typing import List, Dict, Any
import google.generativeai as genai

from src.models.database import settings


class GoogleProvider:
    """Handle requests to Google Gemini API."""
    
    def __init__(self):
        genai.configure(api_key=settings.google_api_key)
        self.base_url = "https://generativelanguage.googleapis.com"
    
    async def send_request(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send chat completion request to Google Gemini.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model ID (e.g., 'gemini-2.0-flash-exp')
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
        
        Returns:
            Dict with response data and metadata
        """
        start_time = time.time()
        
        try:
            # Convert messages to Gemini format
            gemini_messages = []
            for msg in messages:
                role = "user" if msg["role"] in ["user", "system"] else "model"
                gemini_messages.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })
            
            # Get model instance
            model_instance = genai.GenerativeModel(model)
            
            # Generate response
            response = model_instance.generate_content(
                gemini_messages,
                generation_config=genai.GenerationConfig(
                    temperature=kwargs.get("temperature", 0.7),
                    max_output_tokens=kwargs.get("max_tokens", 1024)
                )
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Safety checks
            if not hasattr(response, 'candidates') or not response.candidates:
                return {
                    "success": False,
                    "content": None,
                    "finish_reason": None,
                    "usage": None,
                    "latency_ms": latency_ms,
                    "model": model,
                    "error": "No candidates returned from Google API"
                }
            
            if len(response.candidates) == 0:
                return {
                    "success": False,
                    "content": None,
                    "finish_reason": None,
                    "usage": None,
                    "latency_ms": latency_ms,
                    "model": model,
                    "error": "Empty candidates array from Google API"
                }
            
            candidate = response.candidates[0]
            
            # Safety check for content
            if not hasattr(candidate, 'content') or not candidate.content:
                return {
                    "success": False,
                    "content": None,
                    "finish_reason": None,
                    "usage": None,
                    "latency_ms": latency_ms,
                    "model": model,
                    "error": "No content in candidate from Google API"
                }
            
            if not hasattr(candidate.content, 'parts') or not candidate.content.parts:
                return {
                    "success": False,
                    "content": None,
                    "finish_reason": None,
                    "usage": None,
                    "latency_ms": latency_ms,
                    "model": model,
                    "error": "No parts in content from Google API"
                }
            
            if len(candidate.content.parts) == 0:
                return {
                    "success": False,
                    "content": None,
                    "finish_reason": None,
                    "usage": None,
                    "latency_ms": latency_ms,
                    "model": model,
                    "error": "Empty parts array from Google API"
                }
            
            content = candidate.content.parts[0].text
            
            # Extract token counts with safety checks
            input_tokens = 0
            output_tokens = 0
            
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                input_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0)
                output_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0)
            
            finish_reason = "stop"
            if hasattr(candidate, 'finish_reason'):
                finish_reason = candidate.finish_reason.name if hasattr(candidate.finish_reason, 'name') else str(candidate.finish_reason)
            
            return {
                "success": True,
                "content": content,
                "finish_reason": finish_reason,
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
    
    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for Google models.
        Uses rough approximation of 4 characters per token.
        
        Args:
            text: Text to count tokens for
        
        Returns:
            Estimated number of tokens
        """
        return len(text) // 4