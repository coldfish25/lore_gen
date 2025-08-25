#!/usr/bin/env python3
"""
LoreBot - Astrology Knowledge Automation
Main entry point for the application
"""

import asyncio
from config.settings import Settings
from generator import UniversalGenerator
from utils.logger import setup_logger

async def main():
    """Main function to orchestrate the knowledge generation process"""
    logger = setup_logger("lorebot")
    logger.info("Starting LoreBot knowledge generation")
    
    try:
        # Load configuration
        settings = Settings()
        logger.info("Configuration loaded successfully")
        
        # Create universal generator
        generator = UniversalGenerator(settings)
        
        # Generate zodiac data
        logger.info("Starting zodiac data generation")
        zodiac_results = await generator.generate_data(
            template_path="config/zodiac_prompt.txt",
            base_filename="zodiacs.json",
            data_path="config/zodiac.json"
        )
        
        logger.info("Zodiac data generation completed")
        for language, output_path in zodiac_results.items():
            logger.info(f"Generated {language}: {output_path}")
        
        # Future: Add more data types here
        # planets_results = await generator.generate_data(
        #     template_path="config/planets_prompt.txt",
        #     base_filename="planets.json", 
        #     data_path="config/planets.json"
        # )
        
        logger.info("All data generation completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during generation: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
