"""AI service for image generation using Google Gemini."""
import logging
from google import genai
from google.genai import types
from backend.core.config import Config

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for interacting with Google Gemini AI for image generation."""
    
    def __init__(self):
        """Initialize the Gemini service with API key."""
        Config.validate()
        self.client = genai.Client(api_key=Config.GOOGLE_API_KEY)
        self.model = Config.GEMINI_MODEL

    def generate_image(self, input_image_bytes, prompt):
        """Generate an image based on input image and prompt.
        
        Args:
            input_image_bytes: Raw bytes of the input image
            prompt: Text prompt describing the desired transformation
        
        Returns:
            Raw bytes of generated image, or None if generation fails
        """
        try:
            image_part = types.Part.from_bytes(
                data=input_image_bytes,
                mime_type='image/jpeg'
            )
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=[prompt, image_part],
                config=types.GenerateContentConfig(response_modalities=["IMAGE"])
            )
            
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    return part.inline_data.data
        except Exception:
            logger.exception("Gemini API Error")
            return None
        return None

