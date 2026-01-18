"""
API Clients for Gemini and DeepSeek
"""

import logging
import time
import google.generativeai as genai
from openai import OpenAI
from typing import Optional, Dict, Any

log = logging.getLogger(__name__)


class GeminiClient:
    """Wrapper for Google Gemini API"""
    
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        if not api_key:
            raise ValueError("Google API key is required")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        log.info(f"Gemini client initialized with model: {model}")
    
    def generate(self, prompt: str, max_retries: int = 3, temperature: float = 0.6, **kwargs) -> Optional[str]:
        """Generate text with retry logic"""

        # Translate max_tokens to max_output_tokens for Gemini API
        if 'max_tokens' in kwargs:
            kwargs['max_output_tokens'] = kwargs.pop('max_tokens')

        # Create generation config for temperature and other parameters
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            **kwargs
        )
        
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(
                    prompt, 
                    generation_config=generation_config
                )
                if response and response.text:
                    return response.text
                log.warning(f"Empty response from Gemini (attempt {attempt + 1})")
            except Exception as e:
                log.error(f"Gemini API error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        return None


class DeepSeekClient:
    """Wrapper for DeepSeek API"""
    
    def __init__(self, api_key: str, model: str = "deepseek-reasoner", 
                 base_url: str = "https://api.deepseek.com"):
        if not api_key:
            raise ValueError("DeepSeek API key is required")
        
        # Create client with explicit parameters only
        # This avoids issues with unexpected kwargs like 'proxies'
        try:
            self.client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=120.0,
                max_retries=2
            )
            self.model = model
            log.info(f"DeepSeek client initialized with model: {model}")
        except Exception as e:
            log.error(f"Failed to initialize DeepSeek client: {e}")
            raise
    
    def generate(self, prompt: str, max_tokens: int = 8192, 
                 temperature: float = 0.85, max_retries: int = 3, **kwargs) -> Optional[str]:
        """Generate text with retry logic"""
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )
                if response.choices and response.choices[0].message.content:
                    return response.choices[0].message.content
                log.warning(f"Empty response from DeepSeek (attempt {attempt + 1})")
            except Exception as e:
                log.error(f"DeepSeek API error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        return None