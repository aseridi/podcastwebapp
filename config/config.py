"""
Configuration for Podcast Script Generator - NEW APPROACH
Focus on framework extraction instead of chunking
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent 
OUTPUT_DIR = BASE_DIR / "outputs"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
OUTPUT_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# API Configuration
API_KEYS = {
    "google": os.getenv("GOOGLE_API_KEY"),
    "deepseek": os.getenv("DEEPSEEK_KEY"),
    "google_tts": os.getenv("GOOGLE_TTS_API_KEY"),
}

API_CONFIG = {
    "gemini_model": "gemini-2.5-flash",
    "deepseek_model": "deepseek-reasoner",
    "deepseek_base_url": "https://api.deepseek.com",
    "max_retries": 3,
    "timeout": 120
}

# Pipeline Configuration - NEW APPROACH
PIPELINE_CONFIG = {
    "max_passages": 12,        # Maximum key passages to extract (quotes, analogies, examples)
    "max_examples": 8,         # Maximum supporting examples to extract
    "temperature": 0.85,       # Generation temperature
    "max_tokens": 8192,        # Max tokens per generation
    "section_word_target": 4000,  # Target words per section (3000-5000 range)
}

# Default podcast metadata
PODCAST_META = {
    "name": "My Podcast",
    "host": "Your Name",
    "style": "conversational and engaging, like Philosophize This"
}

# File encodings to try
FILE_ENCODINGS = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")