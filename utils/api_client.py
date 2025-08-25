"""
API client utilities for LLM communication
"""

import asyncio
import aiohttp
from typing import Dict, Any, Optional
import json

class LLMClient:
    """Base client for LLM API communication"""
    
    def __init__(self, api_key: str, model: str = "gpt-4", base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def make_request(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """Make async request to LLM API"""
        if not self.session:
            raise RuntimeError("Client must be used as async context manager")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature
        }
        
        # Use max_completion_tokens for newer models, max_tokens for older ones
        if "gpt-4o" in self.model or "gpt-5" in self.model:
            payload["max_completion_tokens"] = max_tokens
            # gpt-5-mini only supports temperature = 1
            if "gpt-5-mini" in self.model:
                payload.pop("temperature", None)
        else:
            payload["max_tokens"] = max_tokens
        
        async with self.session.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data["choices"][0]["message"]["content"]
            else:
                error_text = await response.text()
                raise Exception(f"API request failed: {response.status} - {error_text}")
    
    async def make_batch_requests(
        self,
        prompts: Dict[str, str],
        delay: float = 1.0,
        **kwargs
    ) -> Dict[str, str]:
        """Make multiple requests with delay between them"""
        results = {}
        
        for key, prompt in prompts.items():
            try:
                result = await self.make_request(prompt, **kwargs)
                results[key] = result
                
                # Add delay between requests to respect rate limits
                if delay > 0:
                    await asyncio.sleep(delay)
                    
            except Exception as e:
                # TODO: Add proper error handling and logging
                results[key] = f"Error: {str(e)}"
        
        return results
