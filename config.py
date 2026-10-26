"""
Configuration module for the AI Children's Story Application.
Manages environment variables, directory paths, file validation limits,
and AI provider settings with safe fallback defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory paths
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    """Base application configuration with secure defaults."""
    
    # Flask Security
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-childrens-story-2025")
    DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    PORT = int(os.getenv("PORT", "5000"))
    
    # Database configuration
    DATABASE_PATH = BASE_DIR / "database" / "storybooks.db"
    
    # Media Storage Directories
    STATIC_DIR = BASE_DIR / "static"
    UPLOAD_FOLDER = STATIC_DIR / "images" / "uploads"
    GENERATED_FOLDER = STATIC_DIR / "images" / "generated"
    AUDIO_FOLDER = STATIC_DIR / "audio"
    PDF_FOLDER = STATIC_DIR / "pdf"
    
    # File Upload Constraints (Security & Resource Protection)
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH_MB", "5")) * 1024 * 1024  # Default 5MB
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
    
    # Story Generation AI Provider Settings
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
    
    # Image Generation AI Provider Settings
    POLLINATIONS_ENABLED = os.getenv("POLLINATIONS_ENABLED", "true").lower() in ("true", "1", "yes")
    HF_TOKEN = os.getenv("HF_TOKEN", "").strip()
    
    # Narration / TTS Settings
    TTS_PROVIDER = os.getenv("TTS_PROVIDER", "gtts").lower()  # Options: 'gtts', 'browser'
    
    # Children's Story Constraints & Presets
    ALLOWED_AGE_GROUPS = ["3–5 years", "6–9 years", "10–12 years"]
    ALLOWED_THEMES = ["friendship", "kindness", "environment", "adventure", "education"]
    ALLOWED_LANGUAGES = ["English", "Spanish", "French", "German", "Hindi"]
    
    # Application Metadata for Disclosures
    APP_NAME = "AI Children's Story Maker"
    APP_VERSION = "1.0.0"
    RESPONSIBLE_AI_DISCLOSURE = (
        "This storybook was co-created using assistive Artificial Intelligence. "
        "All story outlines, character interactions, and illustrations were reviewed, "
        "curated, and edited by human creators to ensure child-safe, age-appropriate, "
        "and uplifting educational storytelling."
    )

    @classmethod
    def ensure_directories(cls):
        """Ensures all required runtime media directories exist."""
        for directory in [
            cls.UPLOAD_FOLDER,
            cls.GENERATED_FOLDER,
            cls.AUDIO_FOLDER,
            cls.PDF_FOLDER,
            cls.DATABASE_PATH.parent,
        ]:
            directory.mkdir(parents=True, exist_ok=True)
