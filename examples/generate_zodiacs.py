#!/usr/bin/env python3
"""
Example script for generating zodiac data
Usage: python examples/generate_zodiacs.py
"""

import asyncio
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from generator import UniversalGenerator

async def main():
    """Generate zodiac data using universal generator"""
    
    # Load settings
    settings = Settings()
    
    # Create generator
    generator = UniversalGenerator(settings)
    
    # Generate zodiac data
    print("Generating zodiac data for all languages...")
    
    results = await generator.generate_data(
        template_path="config/zodiac_prompt.txt",
        base_filename="zodiacs.json",
        data_path="config/zodiac.json"
    )
    
    print("\nGeneration completed!")
    for language, output_path in results.items():
        print(f"  {language}: {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
