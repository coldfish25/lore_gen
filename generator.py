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
                # Complex format (like planets_luminaries.json or houses.json)
                if "planets" in data:
                    return data["planets"]
                elif "houses" in data:
                    return data["houses"]
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
    
    def fill_template_placeholders(self, template: str, data_item: Dict[str, Any], config_data: Dict[str, Any] = None) -> str:
        """Fill template placeholders with data from item"""
        filled_template = template
        
        # Handle special planet data structure
        if "names" in data_item:
            planet_names = data_item["names"]
            # Use English name as default
            if "eng" in planet_names:
                filled_template = filled_template.replace("{planet_name_localized}", planet_names["eng"])
            
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
    
    def get_output_filename(self, base_filename: str) -> str:
        """Generate output filename with eng prefix"""
        # Remove .json extension if present
        if base_filename.endswith('.json'):
            base_filename = base_filename[:-5]
        
        return f"eng_{base_filename}.json"
    
    def check_file_exists(self, filepath: str) -> bool:
        """Check if output file already exists"""
        return os.path.exists(filepath)
    
    async def generate_data(
        self,
        template_path: str,
        base_filename: str,
        data_path: str
    ) -> str:
        """
        Generate data for the specified template and data
        
        Args:
            template_path: Path to prompt template file
            base_filename: Base name for output files
            data_path: Path to data configuration JSON
        
        Returns:
            Output file path
        """
        # Load configurations
        prompt_template = self.load_prompt_template(template_path)
        data_config = self.load_data_config(data_path)
        
        output_filename = self.get_output_filename(base_filename)
        output_path = os.path.join(self.settings.output_dir, output_filename)
        
        # Check if file already exists
        if self.check_file_exists(output_path):
            self.logger.info(f"File {output_path} already exists, skipping")
            return output_path
        
        self.logger.info(f"Generating English data for: {base_filename}")
        
        if self.settings.debug_mode:
            self.logger.info("🔧 DEBUG MODE включен - промпты выводятся в консоль, запросы в LLM не отправляются")
        else:
            self.logger.info("🌍 Отправляем запросы в LLM")
        
        # Process all data items
        results = []
        
        async with LLMClient(
            api_key=self.settings.openai_api_key,
            model=self.settings.openai_model
        ) as client:
            
            for i, data_item in enumerate(data_config):
                key = data_item.get('key', data_item.get('num', f'item_{i}'))
                self.logger.info(f"Processing {key}")
                
                # Fill template with data
                filled_prompt = self.fill_template_placeholders(prompt_template, data_item, data_config)
                
                try:
                    if self.settings.debug_mode:
                        # Debug mode: show prompt and don't send to LLM
                        print(f"\n{'='*60}")
                        print(f"DEBUG PROMPT для {key}:")
                        print(f"{'='*60}")
                        print(filled_prompt)
                        print(f"{'='*60}\n")
                        
                        self.logger.info(f"DEBUG: Промпт показан для {key}, запрос в LLM пропущен")
                        response = f'{{"debug": true, "key": "{key}", "prompt_shown": true}}'
                    else:
                        # Normal mode: send to LLM
                        response = await client.make_request(
                            prompt=filled_prompt,
                            temperature=self.settings.openai_temperature,
                            max_tokens=self.settings.openai_max_tokens
                        )
                    
                    # Add to results
                    results.append({
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
                    results.append({
                        "key": key,
                        "content": f"Error: {str(e)}"
                    })
        
        # Save results to file only if not in debug mode
        if self.settings.debug_mode:
            self.logger.info(f"🔧 DEBUG MODE: Файл НЕ создан (файлы не создаются в debug режиме)")
        else:
            self.save_results(results, output_path)
            self.logger.info(f"Completed generation: {output_path}")
        
        return output_path
    
    def save_results(self, results: List[Dict[str, Any]], output_path: str):
        """Save generated results to JSON file"""
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Prepare output data with metadata
        output_data = {
            "generated_at": self.get_current_timestamp(),
            "language": "eng",
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
        output_path = await generator.generate_data(template_path, base_filename, data_path)
        
        print("Generation completed successfully!")
        print(f"  Output: {output_path}")
            
    except Exception as e:
        print(f"Error during generation: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
