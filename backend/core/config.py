"""Configuration management for the application."""
import os
from dotenv import load_dotenv

load_dotenv()

# Get the project root directory (parent of backend/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Config:
    """Application configuration."""
    
    # API Keys
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    # Lambda CLIP endpoint (optional)
    LAMBDA_CLIP_URL = os.getenv("LAMBDA_CLIP_URL", "https://2ck2fv7t6r3okbukehsmpnzd6y0uqnrz.lambda-url.eu-north-1.on.aws/")
    
    # Flask Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Qdrant Configuration
    QDRANT_URL = os.getenv("QDRANT_URL")
    QDRANT_URL = "https://d5be98a3-6f32-4734-a7bd-844bb4d15180.eu-central-1-0.aws.cloud.qdrant.io"
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    QDRANT_COLLECTION_NAME = "furniture_items"
    
    # Search Service Configuration
    MODEL_ID = "openai/clip-vit-base-patch32"
    
    # AI Service Configuration
    GEMINI_MODEL = "gemini-2.5-flash-image"
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is present."""
        if not cls.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

