#!/usr/bin/env python3
"""Pre-download CLIP model for offline use."""
import logging
import sys
from transformers import CLIPModel, CLIPProcessor
from backend.core.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_model():
    """Download and cache the CLIP model."""
    try:
        logger.info("Downloading CLIP model: %s", Config.MODEL_ID)
        logger.info("This may take a few minutes...")
        
        # Download model (will be cached automatically)
        model = CLIPModel.from_pretrained(Config.MODEL_ID)
        processor = CLIPProcessor.from_pretrained(Config.MODEL_ID)
        
        logger.info("Model downloaded and cached successfully!")
        logger.info("Model cache location: %s", model.config._name_or_path)
        return True
    except Exception as e:
        logger.error("Failed to download model: %s", str(e))
        return False

if __name__ == "__main__":
    success = download_model()
    sys.exit(0 if success else 1)

