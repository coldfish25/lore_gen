#!/usr/bin/env python3
"""
Universal Data Generator for LoreBot
Generates astrology knowledge from templates and data files
"""

import asyncio
import json
import os
import sys
from typing import Dict, List, Any, Optional
from config.settings import Settings
from utils.api_client import LLMClient
from utils.logger import setup_logger

class UniversalGenerator:
    """Universal generator for astrology data using templates and configurations"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = setup_logger("universal_generator")
    
    def load_prompt_template(self, template_path: str) -> str:
        """Load prompt template from file"""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            raise FileNotFoundError(f"Prompt template not found: {template_path}")
    
    def load_data_config(self, data_path: str) -> List[Dict[str, Any]]:
        """Load data configuration from JSON file"""
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Handle different data structures
            if isinstance(data, list):
                # Simple array format (like zodiac.json)
                return data
            elif isinstance(data, dict):
                # Complex format (like planets_luminaries.json)
                if "planets" in data:
                    return data["planets"]
                elif "data" in data:
                    return data["data"]
                else:
                    # Try to extract array from the dict
                    for key, value in data.items():
                        if isinstance(value, list):
                            return value
            
            raise ValueError(f"Unsupported data structure in {data_path}")
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Data config file not found: {data_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in data config: {data_path}")
    
    def fill_template_placeholders(self, template: str, data_item: Dict[str, Any], language_code: str = None, config_data: Dict[str, Any] = None) -> str:
        """Fill template placeholders with data from item"""
        filled_template = template
        
        # Add language information from languages.json
        if language_code:
            languages_config = self.settings.load_languages()
            if language_code in languages_config:
                lang_info = languages_config[language_code]
                filled_template = filled_template.replace("{language_name}", lang_info["name"])
                filled_template = filled_template.replace("{locale_code}", lang_info["locale"])
                # Also support old format
                filled_template = filled_template.replace("{name}", lang_info["name"])
                filled_template = filled_template.replace("{locale}", lang_info["locale"])
        
        # Handle special planet data structure
        if "names" in data_item and language_code:
            planet_names = data_item["names"]
            if language_code in planet_names:
                filled_template = filled_template.replace("{planet_name_localized}", planet_names[language_code])
            
            # Add planet-specific fields
            for key, value in data_item.items():
                if key == "names":
                    continue
                placeholder = f"{{planet_{key}}}"
                if isinstance(value, list):
                    filled_template = filled_template.replace(placeholder, str(value))
                elif value is None:
                    filled_template = filled_template.replace(placeholder, "null")
                else:
                    filled_template = filled_template.replace(placeholder, str(value))
        
        # Replace all other placeholders with data values
        for key, value in data_item.items():
            placeholder = f"{{{key}}}"
            if isinstance(value, (dict, list)):
                filled_template = filled_template.replace(placeholder, str(value))
            elif value is None:
                filled_template = filled_template.replace(placeholder, "null")
            else:
                filled_template = filled_template.replace(placeholder, str(value))
        
        return filled_template
    
    def get_output_filename(self, language_code: str, base_filename: str) -> str:
        """Generate output filename with language prefix"""
        # Remove .json extension if present
        if base_filename.endswith('.json'):
            base_filename = base_filename[:-5]
        
        return f"{language_code}_{base_filename}.json"
    
    def check_file_exists(self, filepath: str) -> bool:
        """Check if output file already exists"""
        return os.path.exists(filepath)
    
    async def generate_data(
        self,
        template_path: str,
        base_filename: str,
        data_path: str,
        languages: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Generate data for all languages and data items
        
        Args:
            template_path: Path to prompt template file
            base_filename: Base name for output files
            data_path: Path to data configuration JSON
            languages: List of language codes to process (if None, use all from config)
        
        Returns:
            Dict mapping language codes to output file paths
        """
        # Load configurations
        prompt_template = self.load_prompt_template(template_path)
        data_config = self.load_data_config(data_path)
        languages_config = self.settings.load_languages()
        
        if languages is None:
            languages = list(languages_config.keys())
        
        results = {}
        
        # Process each language
        for language_code in languages:
            if language_code not in languages_config:
                self.logger.warning(f"Language {language_code} not found in config, skipping")
                continue
            
            output_filename = self.get_output_filename(language_code, base_filename)
            output_path = os.path.join(self.settings.output_dir, output_filename)
            
            # Check if file already exists
            if self.check_file_exists(output_path):
                self.logger.info(f"File {output_path} already exists, skipping")
                results[language_code] = output_path
                continue
            
            self.logger.info(f"Generating data for language: {language_code}")
            
            if self.settings.debug_mode:
                self.logger.info("🔧 DEBUG MODE включен - промпты выводятся в консоль, запросы в LLM не отправляются")
            else:
                self.logger.info("� Отправляем запросы в LLM")
            
            # Process all data items for this language
            language_results = []
            
            async with LLMClient(
                api_key=self.settings.openai_api_key,
                model=self.settings.openai_model
            ) as client:
                
                for i, data_item in enumerate(data_config):
                    key = data_item.get('key', f'item_{i}')
                    self.logger.info(f"Processing {key} for {language_code}")
                    
                    # Fill template with data
                    filled_prompt = self.fill_template_placeholders(prompt_template, data_item, language_code, data_config)
                    
                    # Add language instruction
                    language_instruction = self.settings.get_language_description(language_code)
                    final_prompt = f"{language_instruction}\n\n{filled_prompt}"
                    
                    try:
                        if self.settings.debug_mode:
                            # Debug mode: show prompt and don't send to LLM
                            print(f"\n{'='*60}")
                            print(f"DEBUG PROMPT для {key} ({language_code}):")
                            print(f"{'='*60}")
                            print(final_prompt)
                            print(f"{'='*60}\n")
                            
                            self.logger.info(f"DEBUG: Промпт показан для {key}, запрос в LLM пропущен")
                            response = f'{{"debug": true, "key": "{key}", "language": "{language_code}", "prompt_shown": true}}'
                        else:
                            # Normal mode: send to LLM without showing prompt
                            response = await client.make_request(
                                prompt=final_prompt,
                                temperature=self.settings.openai_temperature,
                                max_tokens=self.settings.openai_max_tokens
                            )
                        
                        # Add to results
                        language_results.append({
                            "key": key,
                            "content": response.strip()
                        })
                        
                        if self.settings.debug_mode:
                            self.logger.info(f"✅ DEBUG: Промпт протестирован для {key}")
                        else:
                            self.logger.info(f"✅ Successfully processed {key}")
                        
                        # Add delay between requests (only in normal mode, not in debug)
                        if not self.settings.debug_mode and self.settings.delay_between_requests > 0:
                            await asyncio.sleep(self.settings.delay_between_requests)
                            
                    except Exception as e:
                        self.logger.error(f"Error processing {key}: {str(e)}")
                        language_results.append({
                            "key": key,
                            "content": f"Error: {str(e)}"
                        })
            
            # Save results to file only if not in debug mode
            if self.settings.debug_mode:
                self.logger.info(f"🔧 DEBUG MODE: Файл НЕ создан для {language_code} (файлы не создаются в debug режиме)")
            else:
                self.save_results(language_results, output_path, language_code)
                self.logger.info(f"Completed generation for {language_code}: {output_path}")
            
            results[language_code] = output_path
        
        return results
    
    def save_results(self, results: List[Dict[str, Any]], output_path: str, language_code: str):
        """Save generated results to JSON file"""
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Prepare output data with metadata
        output_data = {
            "generated_at": self.get_current_timestamp(),
            "language": language_code,
            "total_items": len(results),
            "data": results
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    def get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat()


async def main():
    """Main function for command-line usage"""
    if len(sys.argv) != 4:
        print("Usage: python generator.py <template_path> <base_filename> <data_path>")
        print("Example: python generator.py config/zodiac_prompt.txt zodiacs config/zodiac.json")
        sys.exit(1)
    
    template_path = sys.argv[1]
    base_filename = sys.argv[2]
    data_path = sys.argv[3]
    
    # Load settings
    settings = Settings()
    
    # Create generator
    generator = UniversalGenerator(settings)
    
    # Generate data
    try:
        results = await generator.generate_data(template_path, base_filename, data_path)
        
        print("Generation completed successfully!")
        for language, output_path in results.items():
            print(f"  {language}: {output_path}")
            
    except Exception as e:
        print(f"Error during generation: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
