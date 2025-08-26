"""
Configuration settings for LoreBot
"""

import os
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

@dataclass
class Settings:
    """Application settings configuration"""
    
    # OpenAI API Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    openai_temperature: float = 0.7
    openai_max_tokens: int = 2000
    
    # Translation Configuration
    openai_translation_model: str = "gpt-4o-mini"
    openai_translation_max_tokens: int = 2000
    
    # Output Configuration
    output_dir: str = "data"
    
    # Zodiac Configuration
    zodiac_config_path: str = "config/zodiac.json"
    
    # Processing Configuration
    batch_size: int = 5
    delay_between_requests: float = 1.0  # seconds
    
    # Debug Configuration
    debug_mode: bool = False
    
    def __post_init__(self):
        """Load settings from environment variables"""
        # Try to load from .env file first
        try:
            from dotenv import load_dotenv
            load_dotenv("config/config.env")
        except ImportError:
            pass  # python-dotenv not installed
        except Exception:
            pass  # file not found or other error
        
        self.openai_api_key = os.getenv("OPENAI_API_KEY", self.openai_api_key)
        self.openai_model = os.getenv("OPENAI_MODEL", self.openai_model)
        self.openai_temperature = float(os.getenv("OPENAI_TEMPERATURE", self.openai_temperature))
        self.openai_max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", self.openai_max_tokens))
        self.openai_translation_model = os.getenv("OPENAI_TRANSLATION_MODEL", self.openai_translation_model)
        self.openai_translation_max_tokens = int(os.getenv("OPENAI_TRANSLATION_MAX_TOKENS", self.openai_translation_max_tokens))
        self.output_dir = os.getenv("OUTPUT_DIR", self.output_dir)
        self.zodiac_config_path = os.getenv("ZODIAC_CONFIG", self.zodiac_config_path)
        self.batch_size = int(os.getenv("BATCH_SIZE", self.batch_size))
        self.delay_between_requests = float(os.getenv("DELAY_BETWEEN_REQUESTS", self.delay_between_requests))
        self.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
        
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY must be set in environment variables or config")
    
    def load_zodiac_config(self) -> List[Dict[str, Any]]:
        """Load zodiac configuration from JSON file"""
        try:
            with open(self.zodiac_config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Zodiac config file not found: {self.zodiac_config_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in zodiac config: {self.zodiac_config_path}")
    
    def get_zodiac_info(self, zodiac_key: str) -> Dict[str, Any]:
        """Get zodiac information by key"""
        zodiac_config = self.load_zodiac_config()
        
        for zodiac in zodiac_config:
            if zodiac["key"] == zodiac_key:
                return zodiac
                
        raise ValueError(f"Zodiac key '{zodiac_key}' not found in config")
    
    @classmethod
    def load_from_file(cls, config_path: str = "config/config.env"):
        """Load configuration from file"""
        # TODO: Implement loading from .env file
        return cls()
