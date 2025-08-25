"""
Base processor class for all astrology knowledge processors
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import json
import os
from datetime import datetime

class BaseProcessor(ABC):
    """Base class for all astrology knowledge processors"""
    
    def __init__(self, settings, output_dir: str = "data"):
        self.settings = settings
        self.output_dir = output_dir
        self.ensure_output_dir()
    
    def ensure_output_dir(self):
        """Ensure output directory exists"""
        os.makedirs(self.output_dir, exist_ok=True)
    
    @abstractmethod
    def get_prompts(self, language_code: str = None) -> Dict[str, str]:
        """Return dictionary of prompts for this processor in specified language"""
        pass
    
    @abstractmethod
    def process_response(self, prompt_key: str, response: str, language_code: str = None) -> Dict[str, Any]:
        """Process LLM response and return structured data"""
        pass
    
    @abstractmethod
    def get_output_filename(self, prompt_key: str, language_code: str = None) -> str:
        """Return filename for saving the processed data"""
        pass
    
    def get_language_prompt_template(self, language_code: str = None) -> str:
        """Get language-specific instruction for prompts"""
        if language_code is None:
            language_code = self.settings.default_language
        
        return self.settings.get_language_description(language_code)
    
    def format_prompt_with_language(self, base_prompt: str, language_code: str = None) -> str:
        """Format prompt with language instruction"""
        language_instruction = self.get_language_prompt_template(language_code)
        
        return f"""{language_instruction}

{base_prompt}

Please ensure all content is generated in the specified language and follows cultural context appropriate for that language."""
    
    def save_to_json(self, data: Dict[str, Any], filename: str, language_code: str = None):
        """Save data to JSON file with metadata"""
        filepath = os.path.join(self.output_dir, filename)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Add metadata
        output_data = {
            "generated_at": datetime.now().isoformat(),
            "processor": self.__class__.__name__,
            "language": language_code or self.settings.default_language,
            "data": data
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    async def process_all(self, language_code: str = None):
        """Process all prompts for this processor in specified language"""
        # TODO: Implement async processing with LLM calls
        prompts = self.get_prompts(language_code)
        
        for prompt_key, prompt_text in prompts.items():
            # TODO: Make LLM request
            # formatted_prompt = self.format_prompt_with_language(prompt_text, language_code)
            # response = await self.make_llm_request(formatted_prompt)
            # processed_data = self.process_response(prompt_key, response, language_code)
            # filename = self.get_output_filename(prompt_key, language_code)
            # self.save_to_json(processed_data, filename, language_code)
            pass
