"""
Narration Service.
Manages storybook text-to-speech narration.
Provides:
1. Server-side MP3 generation using gTTS (Google Text-to-Speech, free tier, no API key needed).
2. Distinction between downloadable audio files and browser Web Speech API synthesis.
"""

import os
import logging
from pathlib import Path
from gtts import gTTS
from config import Config

logger = logging.getLogger(__name__)

class NarrationService:
    @classmethod
    def generate_storybook_audio(cls, storybook_id, title, pages, lang="en"):
        """
        Synthesizes the complete storybook audio into a standalone MP3 file.
        Includes title, page narration, and moral takeaway.
        Saves the file to static/audio/storybook_<id>.mp3.
        Returns the relative web path or raises an exception.
        """
        Config.ensure_directories()
        
        # Build narration script
        narration_parts = [f"Story title: {title}."]
        for p in pages:
            page_num = p.get("page_number", "")
            text = p.get("text", "").strip()
            if text:
                narration_parts.append(f"Page {page_num}. {text}")
        
        full_text = " ... ".join(narration_parts)
        if not full_text.strip():
            raise ValueError("No story text available to synthesize.")

        filename = f"storybook_{storybook_id}.mp3"
        destination = Config.AUDIO_FOLDER / filename
        
        # Map languages
        lang_code = "en"
        lang_lower = str(lang).lower()
        if "span" in lang_lower:
            lang_code = "es"
        elif "fren" in lang_lower:
            lang_code = "fr"
        elif "germ" in lang_lower:
            lang_code = "de"
        elif "hind" in lang_lower:
            lang_code = "hi"

        try:
            tts = gTTS(text=full_text, lang=lang_code, slow=False)
            tts.save(str(destination))
            return f"audio/{filename}"
        except Exception as e:
            logger.error(f"Failed to generate gTTS narration: {e}")
            raise RuntimeError(f"Narration generation encountered an error: {str(e)}")

    @classmethod
    def get_audio_status(cls, storybook_id):
        """
        Checks whether a server-side audio recording file exists for this storybook.
        """
        filename = f"storybook_{storybook_id}.mp3"
        destination = Config.AUDIO_FOLDER / filename
        exists = destination.exists() and destination.is_file() and destination.stat().st_size > 0
        return {
            "has_audio_file": exists,
            "audio_web_path": f"audio/{filename}" if exists else None,
            "browser_synthesis_supported": True # Supported natively in all modern browsers
        }
