"""
Streamlined configuration for Podcast Script Generator
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
    "google_tts" : os.getenv("GOOGLE_TTS_API_KEY"),
}

API_CONFIG = {
    "gemini_model": "gemini-2.5-flash",
    "deepseek_model": "deepseek-reasoner",
    "deepseek_base_url": "https://api.deepseek.com",
    "max_retries": 3,
    "timeout": 120
}

# Pipeline Configuration for Books
PIPELINE_CONFIG = {
    "max_chapters": 20,        # Changed from max_concepts
    "chunk_size": 3000,        # Larger chunks for books
    "min_chunk_size": 1000,    # Larger minimum
    "temperature": 0.85,
    "max_tokens": 8192,
    "section_word_target": 4000,  # Target 3000-5000 words per section
}

# Default podcast metadata
PODCAST_META = {
    "name": "My Podcast",
    "host": "Your Name",
    "style": "conversational and engaging"
}

# File encodings to try
FILE_ENCODINGS = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
