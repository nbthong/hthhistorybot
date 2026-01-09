import os
import logging
from typing import Any, Optional, Iterator
from dotenv import load_dotenv
from google import genai
from google.genai import types
from app.utils.config import PREFERRED_MODEL, TEXT_GENERATION_CONFIG, TEXT_GENERATION_CONFIG_STREAM, ENV_FILE, MODEL_GEN_IMAGE
import base64

logger = logging.getLogger(__name__)

load_dotenv(ENV_FILE)

API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()

class GeminiKeyManager:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None, generation_config: Optional[dict[str, Any]] = None, stream_config: Optional[dict[str, Any]] = None):
        self.api_key: str = api_key or API_KEY
        self.model_name: str = model_name or PREFERRED_MODEL
        self.generation_config: types.GenerateContentConfig = generation_config or TEXT_GENERATION_CONFIG
        self.stream_config: types.GenerateContentConfig = stream_config or TEXT_GENERATION_CONFIG_STREAM
        self.client = genai.Client(api_key=self.api_key)

    def generate_content(self, contents: Any, **kwargs: Any):
        return self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=self.generation_config,
            **kwargs,
        )

    def stream_content(self, contents: Any, use_stream_config: bool = True, **kwargs: Any) -> Iterator[str]:
        for chunk in self.client.models.generate_content_stream(
            model=self.model_name,
            contents=contents,
            config=self.stream_config,
            **kwargs,
        ):
            text = getattr(chunk, "text", None)
            if text:
                yield text
                continue
            try:
                parts = chunk.candidates[0].content.parts or []
                merged = "".join(p.text for p in parts if getattr(p, "text", None))
                if merged:
                    yield merged
            except Exception:
                continue

    def generate_image(self, prompt: str) -> tuple[str, str] | None:
        try:
            response = self.client.models.generate_content(
                model=MODEL_GEN_IMAGE,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                ),
            )

            if response.parts:
                for part in response.parts:
                    if part.inline_data:
                        mime_type = part.inline_data.mime_type or "application/octet-stream"
                        logger.info(f"✅ Image generated successfully (Mime: {mime_type})")
                        image_bytes = part.inline_data.data
                        return (mime_type, base64.b64encode(image_bytes).decode("utf-8"))
            
            logger.warning("⚠️ No image part found in response")
            return None

        except Exception as e:
            logger.error(f"❌ Image generation failed: {e}")
            return None

if API_KEY:
    key_manager = GeminiKeyManager()
else:
    key_manager = None
    logging.warning("No API key found! Please set GOOGLE_API_KEY in environment variables.")