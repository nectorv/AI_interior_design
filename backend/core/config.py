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
    
    # Flask Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Search Service Configuration
    CSV_FILE = os.path.join(PROJECT_ROOT, "google_dataset", "interior_design_dataset.csv")
    EMBEDDINGS_FILE = os.path.join(PROJECT_ROOT, "google_dataset", "embeddings.pkl")
    MODEL_ID = "openai/clip-vit-base-patch32"
    
    # AI Service Configuration
    GEMINI_MODEL = "gemini-2.5-flash-image"
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is present."""
        if not cls.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

