"""Image encoding and decoding utilities for frontend communication."""
import base64
import logging
import re

logger = logging.getLogger(__name__)


def process_image_for_frontend(image_bytes):
    """Converts raw image bytes to a data URI string for HTML.
    
    Args:
        image_bytes: Raw image bytes
    
    Returns:
        Data URI string (e.g., 'data:image/png;base64,...') or None
    """
    if not image_bytes:
        return None
    b64_string = base64.b64encode(image_bytes).decode('utf-8')
    return f'data:image/png;base64,{b64_string}'


def decode_frontend_image(uri):
    """Converts frontend data URI back to raw bytes.
    
    Args:
        uri: Data URI string from frontend
    
    Returns:
        Raw image bytes or None if decoding fails
    """
    try:
        if not uri:
            return None
        image_data = re.sub('^data:image/.+;base64,', '', uri)
        return base64.b64decode(image_data)
    except Exception:
        logger.exception("Decoding error")
        return None

