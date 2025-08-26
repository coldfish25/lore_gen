#!/usr/bin/env python3
"""
Translation Script for LoreBot
Translates existing data files to supported languages
"""

import asyncio
import json
import os
import sys
from typing import Dict, List, Any, Optional
from config.settings import Settings
from utils.api_client import LLMClient
from utils.logger import setup_logger

class DataTranslator:
    """Translates astrology data files to supported languages"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = setup_logger("data_translator")
    
    def load_support_languages(self) -> Dict[str, Any]:
        """Load supported languages configuration"""
        try:
            with open('config/support_languages.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError("config/support_languages.json not found")
    
    def load_translation_prompt(self) -> str:
        """Load translation prompt template"""
        try:
            with open('config/translation_prompt.txt', 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            raise FileNotFoundError("config/translation_prompt.txt not found")
    
    def validate_source_file(self, source_data: Dict[str, Any]) -> bool:
        """Validate source file structure and content JSON"""
        if "data" not in source_data:
            raise ValueError("Source file missing 'data' field")
        
        self.logger.info("🔍 Validating source file content...")
        
        invalid_items = []
        for item in source_data["data"]:
            if "content" not in item:
                invalid_items.append((item.get("key", "unknown"), "Missing 'content' field"))
                continue
                
            try:
                content = json.loads(item["content"])
                required_fields = ["title", "one_liner", "body_md"]
                missing_fields = [field for field in required_fields if field not in content]
                
                if missing_fields:
                    invalid_items.append((item.get("key", "unknown"), f"Missing fields: {missing_fields}"))
                    
            except json.JSONDecodeError as e:
                invalid_items.append((item.get("key", "unknown"), f"Invalid JSON: {str(e)}"))
        
        if invalid_items:
            self.logger.error("❌ Source file validation failed!")
            for key, error in invalid_items:
                self.logger.error(f"  - Item {key}: {error}")
            raise ValueError(f"Source file has {len(invalid_items)} invalid items")
        
        self.logger.info("✅ Source file validation passed - all items are valid")
        return True
    
    def validate_translated_content(self, translated_content: str, item_key: str) -> bool:
        """Validate translated JSON content"""
        try:
            content = json.loads(translated_content)
            required_fields = ["title", "one_liner", "body_md"]
            
            # Check for missing fields
            missing_fields = [field for field in required_fields if field not in content]
            if missing_fields:
                self.logger.warning(f"⚠️  Translated content for {item_key} missing fields: {missing_fields}")
                return False
            
            # Check for empty fields
            empty_fields = [field for field in required_fields if not content[field].strip()]
            if empty_fields:
                self.logger.warning(f"⚠️  Translated content for {item_key} has empty fields: {empty_fields}")
                return False
            
            return True
            
        except json.JSONDecodeError as e:
            self.logger.warning(f"⚠️  Translated content for {item_key} is not valid JSON: {str(e)}")
            return False
    
    def load_source_file(self, filename: str) -> Dict[str, Any]:
        """Load the source data file to translate"""
        filepath = os.path.join("data", filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source_data = json.load(f)
            
            # Validate source file before proceeding
            self.validate_source_file(source_data)
            return source_data
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Source file {filepath} not found")
    
    def get_target_filename(self, source_filename: str, target_locale: str) -> str:
        """Generate target filename with locale prefix"""
        # Remove existing locale prefix if present (e.g., eng_planets.json -> planets.json)
        if source_filename.startswith('eng_'):
            base_filename = source_filename[4:]  # Remove 'eng_' prefix
        else:
            base_filename = source_filename
        
        return f"{target_locale}_{base_filename}"
    
    def file_exists(self, filename: str) -> bool:
        """Check if target file already exists"""
        filepath = os.path.join("data", filename)
        return os.path.exists(filepath)
    
    def fill_translation_prompt(self, template: str, content: str, target_lang_name: str) -> str:
        """Fill translation prompt template with content and target language"""
        return template.replace("{content}", content).replace("{target_lang_name}", target_lang_name)
    
    async def translate_content(self, content: str, target_lang_name: str) -> str:
        """Translate content using LLM"""
        template = self.load_translation_prompt()
        prompt = self.fill_translation_prompt(template, content, target_lang_name)
        
        if self.settings.debug_mode:
            print(f"\n{'='*60}")
            print(f"TRANSLATION PROMPT для {target_lang_name}:")
            print(f"{'='*60}")
            print(prompt)
            print(f"{'='*60}\n")
            return f"[DEBUG] Translated to {target_lang_name}"
        
        async with LLMClient(
            api_key=self.settings.openai_api_key,
            model=self.settings.openai_translation_model
        ) as client:
            response = await client.make_request(
                prompt=prompt,
                temperature=0.3,  # Lower temperature for translation consistency
                max_tokens=self.settings.openai_translation_max_tokens
            )
            return response.strip()
    
    async def translate_data_item(self, item: Dict[str, Any], target_lang_name: str) -> Dict[str, Any]:
        """Translate a single data item"""
        translated_item = item.copy()
        
        # Extract and translate the content field
        if 'content' in item:
            try:
                # Parse the content as JSON
                content_json = json.loads(item['content'])
                self.logger.info(f"Translating content for {item.get('key', 'unknown')} to {target_lang_name}")
                
                # Translate the entire JSON object (title, one_liner, and body_md)
                content_str = json.dumps(content_json, ensure_ascii=False, indent=2)
                translated_content_str = await self.translate_content(content_str, target_lang_name)
                
                # Validate translated content
                item_key = item.get('key', 'unknown')
                if not self.validate_translated_content(translated_content_str, item_key):
                    self.logger.warning(f"⚠️  Using original content for {item_key} due to translation validation failure")
                    translated_item['content'] = item['content']
                else:
                    # Parse the translated JSON and update the content
                    try:
                        translated_content_json = json.loads(translated_content_str)
                        translated_item['content'] = json.dumps(translated_content_json, ensure_ascii=False)
                        self.logger.info(f"✅ Successfully translated and validated content for {item_key}")
                    except json.JSONDecodeError:
                        self.logger.warning(f"⚠️  Failed to parse translated JSON for {item_key}, using original")
                        translated_item['content'] = item['content']
                
                # Add delay between requests if not in debug mode
                if not self.settings.debug_mode and self.settings.delay_between_requests > 0:
                    await asyncio.sleep(self.settings.delay_between_requests)
                        
            except json.JSONDecodeError:
                self.logger.error(f"Failed to parse content JSON for {item.get('key', 'unknown')}")
                
        return translated_item
    
    def save_translated_file(self, translated_data: Dict[str, Any], target_filename: str, target_locale: str):
        """Save translated data to file"""
        output_path = os.path.join("data", target_filename)
        
        # Update metadata
        translated_data['language'] = target_locale
        translated_data['generated_at'] = translated_data.get('generated_at', '')
        
        if self.settings.debug_mode:
            self.logger.info(f"🔧 DEBUG MODE: Файл НЕ создан - {output_path}")
            return
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(translated_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"✅ Translated file saved: {output_path}")
    
    async def translate_file(self, source_filename: str):
        """Translate a source file to all supported languages"""
        self.logger.info(f"Starting translation process for: {source_filename}")
        
        # Load configurations
        support_languages = self.load_support_languages()
        source_data = self.load_source_file(source_filename)  # This now includes validation
        
        if self.settings.debug_mode:
            self.logger.info("🔧 DEBUG MODE включен - переводы показываются в консоль, файлы не создаются")
        else:
            self.logger.info("🌍 Начинаем перевод на поддерживаемые языки")
        
        # Process each supported language
        for locale, lang_config in support_languages.items():
            target_filename = self.get_target_filename(source_filename, locale)
            
            # Check if target file already exists
            if not self.settings.debug_mode and self.file_exists(target_filename):
                self.logger.info(f"⏭️  File {target_filename} already exists, skipping")
                continue
            
            self.logger.info(f"🔄 Translating to {lang_config['name']} ({locale})")
            
            # Create translated data structure
            translated_data = {
                "generated_at": source_data.get("generated_at", ""),
                "language": locale,
                "total_items": source_data.get("total_items", 0),
                "data": []
            }
            
            # Translate each data item
            for item in source_data.get("data", []):
                translated_item = await self.translate_data_item(item, lang_config['name'])
                translated_data["data"].append(translated_item)
            
            # Save translated file
            self.save_translated_file(translated_data, target_filename, locale)
        
        self.logger.info(f"✅ Translation completed for: {source_filename}")

async def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python3 translator.py <source_filename>")
        print("Example: python3 translator.py eng_planets_luminaries.json")
        sys.exit(1)
    
    source_filename = sys.argv[1]
    
    # Initialize settings and translator
    settings = Settings()
    translator = DataTranslator(settings)
    
    try:
        await translator.translate_file(source_filename)
        print(f"\n🎉 Translation process completed for {source_filename}!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
