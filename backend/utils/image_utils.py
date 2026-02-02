"""Image encoding and decoding utilities for frontend communication."""
import base64
import io
import logging
import re
from PIL import Image

logger = logging.getLogger(__name__)


def detect_image_mime_type(image_bytes):
    """Detect the MIME type of an image from its bytes.
    
    Args:
        image_bytes: Raw image bytes
    
    Returns:
        MIME type string (e.g., 'image/jpeg', 'image/png'), or 'image/png' as fallback
    """
    if not image_bytes:
        return 'image/png'
    
    try:
        img = Image.open(io.BytesIO(image_bytes))
        format_lower = img.format.lower() if img.format else ''
        
        # Map PIL format names to MIME types
        format_to_mime = {
            'jpeg': 'image/jpeg',
            'jpg': 'image/jpeg',
            'png': 'image/png',
            'webp': 'image/webp',
            'gif': 'image/gif',
        }
        
        mime_type = format_to_mime.get(format_lower, 'image/png')
        return mime_type
    except Exception:
        logger.exception("Error detecting image format, defaulting to PNG")
        return 'image/png'


def process_image_for_frontend(image_bytes):
    """Converts raw image bytes to a data URI string for HTML.
    
    Args:
        image_bytes: Raw image bytes
    
    Returns:
        Data URI string (e.g., 'data:image/png;base64,...' or 'data:image/jpeg;base64,...') or None
    """
    if not image_bytes:
        return None
    mime_type = detect_image_mime_type(image_bytes)
    b64_string = base64.b64encode(image_bytes).decode('utf-8')
    return f'data:{mime_type};base64,{b64_string}'


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
