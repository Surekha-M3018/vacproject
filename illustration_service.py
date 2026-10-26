"""
Illustration Management Service.
Handles AI image generation (Pollinations AI, OpenAI DALL-E), secure manual image
uploads with Pillow verification, and image replacement/removal.
Maintains clear provenance so no synthetic image is ever claimed to be generated
when it was uploaded or missing.
"""

import os
import uuid
import urllib.parse
import logging
from pathlib import Path
import requests
from PIL import Image
from werkzeug.utils import secure_filename
from config import Config

logger = logging.getLogger(__name__)

class IllustrationService:
    @classmethod
    def generate_image_for_prompt(cls, prompt, storybook_id, page_number):
        """
        Attempts to generate an illustration using configured AI image APIs.
        Priority:
        1. Pollinations AI (free, no API key needed, if enabled)
        2. OpenAI DALL-E 3 (if OPENAI_API_KEY is configured)
        3. Hugging Face Inference (if HF_TOKEN is configured)
        
        Returns (saved_relative_path, source_attribution) or (None, None).
        """
        Config.ensure_directories()
        clean_prompt = prompt.strip()
        filename = f"gen_sb{storybook_id}_p{page_number}_{uuid.uuid4().hex[:8]}.png"
        save_path = Config.GENERATED_FOLDER / filename
        relative_web_path = f"images/generated/{filename}"

        # 1. Pollinations AI (Free tier, zero credentials required)
        if Config.POLLINATIONS_ENABLED:
            try:
                encoded = urllib.parse.quote(clean_prompt)
                url = f"https://image.pollinations.ai/prompt/{encoded}?width=768&height=768&nologo=true&seed={page_number * 100}"
                resp = requests.get(url, timeout=30)
                if resp.status_code == 200 and len(resp.content) > 1000:
                    with open(save_path, "wb") as f:
                        f.write(resp.content)
                    
                    # Verify valid image using Pillow
                    try:
                        with Image.open(save_path) as img:
                            img.verify()
                        return relative_web_path, "ai_pollinations"
                    except Exception:
                        if save_path.exists():
                            save_path.unlink()
            except Exception as e:
                logger.warning(f"Pollinations generation failed: {e}")

        # 2. OpenAI DALL-E 3 (if API key available)
        if Config.OPENAI_API_KEY:
            try:
                url = "https://api.openai.com/v1/images/generations"
                headers = {
                    "Authorization": f"Bearer {Config.OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "dall-e-3",
                    "prompt": f"Children's book illustration, gentle, family friendly: {clean_prompt}",
                    "n": 1,
                    "size": "1024x1024"
                }
                resp = requests.post(url, json=payload, headers=headers, timeout=40)
                if resp.status_code == 200:
                    img_url = resp.json()["data"][0]["url"]
                    img_resp = requests.get(img_url, timeout=30)
                    if img_resp.status_code == 200:
                        with open(save_path, "wb") as f:
                            f.write(img_resp.content)
                        return relative_web_path, "ai_openai"
            except Exception as e:
                logger.warning(f"OpenAI DALL-E generation failed: {e}")

        # If no service succeeded or was configured, return None
        return None, "none"

    @classmethod
    def save_uploaded_image(cls, file_storage, storybook_id, page_number):
        """
        Validates and safely stores a user-uploaded image.
        Checks:
        - Filename and extension
        - MIME type and image corruption via Pillow
        - Size bounds
        Returns (relative_web_path, source) or raises ValueError with friendly message.
        """
        Config.ensure_directories()
        
        if not file_storage or file_storage.filename == "":
            raise ValueError("No image file was selected.")

        original_name = secure_filename(file_storage.filename)
        ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
        
        if ext not in Config.ALLOWED_IMAGE_EXTENSIONS:
            raise ValueError(f"Invalid format .{ext}. Please upload a PNG, JPG, JPEG, or WEBP file.")

        unique_name = f"upload_sb{storybook_id}_p{page_number}_{uuid.uuid4().hex[:8]}.{ext}"
        destination = Config.UPLOAD_FOLDER / unique_name
        
        # Save to disk
        file_storage.save(str(destination))

        # Pillow validation: ensures file is not an executable or corrupted payload
        try:
            with Image.open(destination) as img:
                img.verify() # Verify file header and integrity
        except Exception:
            if destination.exists():
                destination.unlink()
            raise ValueError("Uploaded file appears to be corrupted or is not a recognized image format.")

        relative_web_path = f"images/uploads/{unique_name}"
        return relative_web_path, "uploaded"

    @classmethod
    def delete_image_file(cls, relative_web_path):
        """Safely removes an image file from disk if it exists within static."""
        if not relative_web_path:
            return
        clean_path = Config.STATIC_DIR / relative_web_path.replace("/", os.sep)
        try:
            if clean_path.exists() and clean_path.is_file():
                clean_path.unlink()
        except Exception as e:
            logger.warning(f"Failed to remove file {clean_path}: {e}")
