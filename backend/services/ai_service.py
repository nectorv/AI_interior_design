"""AI service for image generation using Google Gemini."""
import logging
from google import genai
from google.genai import types
from backend.core.config import Config
from backend.utils.image_utils import detect_image_mime_type

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
            # Detect the actual image format from bytes
            mime_type = detect_image_mime_type(input_image_bytes)
            image_part = types.Part.from_bytes(
                data=input_image_bytes,
                mime_type=mime_type
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

