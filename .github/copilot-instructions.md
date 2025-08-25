# LoreBot - Astrology Knowledge Automation

This is a Python project for automating LLM requests to generate astrology knowledge and save it to JSON files.

## Project Structure
- Main entry point: `main.py`
- Configuration: `config/`
- Data processors: `processors/`
- Output storage: `data/`
- Utilities: `utils/`

## Setup Instructions
1. Copy `config/config.env.example` to `config/config.env`
2. Add your OpenAI API key to the config file
3. Run `python3 main.py` to start the application

## Architecture
- **BaseProcessor**: Abstract base class for all knowledge processors
- **ZodiacProcessor**: Handles zodiac signs data generation
- **LLMClient**: Async client for OpenAI API communication
- **Settings**: Configuration management with environment variables

## Expansion
To add new astrology categories, create new processors inheriting from BaseProcessor and implement the required methods.

Project setup completed successfully!
