"""
Zodiac signs processor for generating astrology knowledge
"""

from typing import Dict, List, Any
from .base_processor import BaseProcessor

class ZodiacProcessor(BaseProcessor):
    """Processor for zodiac signs astrology knowledge"""
    
    def __init__(self, settings, output_dir: str = "data"):
        super().__init__(settings, output_dir)
        self.zodiac_config = settings.load_zodiac_config()
        self.zodiac_signs = [zodiac["key"] for zodiac in self.zodiac_config]
    
    def get_prompts(self, language_code: str = None) -> Dict[str, str]:
        """Generate prompts for each zodiac sign in specified language"""
        prompts = {}
        
        for sign_key in self.zodiac_signs:
            # Get zodiac info from config
            sign_info = self.settings.get_zodiac_info(sign_key)
            
            prompts[f"{sign_key}_general"] = f"""
            Provide comprehensive astrology information about {sign_key.title()} ({sign_info['emoji']}) zodiac sign including:
            - Element: {sign_info['element']} and modality: {sign_info['modality']}
            - Ruling planet: {sign_info['ruler']}
            - Key personality traits
            - Strengths and weaknesses
            - Compatible signs
            - Career tendencies
            - Health considerations
            
            Format the response as detailed, accurate astrological knowledge.
            """
            
            prompts[f"{sign_key}_daily"] = f"""
            Generate a template for daily horoscope for {sign_key.title()} ({sign_info['emoji']}) that includes:
            - General mood and energy
            - Love and relationships
            - Career and finance
            - Health and wellness
            - Lucky numbers and colors
            
            Make it generic enough to be customizable but specific to {sign_key.title()} traits.
            """
        
        return prompts
    
    def process_response(self, prompt_key: str, response: str, language_code: str = None) -> Dict[str, Any]:
        """Process LLM response for zodiac data"""
        sign_key = prompt_key.split('_')[0]
        info_type = '_'.join(prompt_key.split('_')[1:])
        
        # Get zodiac info from config
        zodiac_info = self.settings.get_zodiac_info(sign_key)
        
        return {
            "zodiac_sign": sign_key,
            "info_type": info_type,
            "language": language_code or self.settings.default_language,
            "content": response.strip(),
            "metadata": {
                "sign_element": zodiac_info["element"],
                "sign_modality": zodiac_info["modality"],
                "ruler": zodiac_info["ruler"],
                "emoji": zodiac_info["emoji"]
            }
        }
    
    def get_output_filename(self, prompt_key: str, language_code: str = None) -> str:
        """Generate filename for zodiac data with language code"""
        sign_name = prompt_key.split('_')[0]
        info_type = '_'.join(prompt_key.split('_')[1:])
        lang = language_code or self.settings.default_language
        return f"zodiac/{lang}/{sign_name}_{info_type}.json"
