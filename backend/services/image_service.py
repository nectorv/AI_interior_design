"""Image processing service for handling image operations."""
import io
import logging
from PIL import Image
from backend.utils.image_utils import decode_frontend_image

logger = logging.getLogger(__name__)


def crop_image_from_data_uri(image_data_uri, crop_box):
    """Crop an image from a data URI based on crop coordinates.
    
    Args:
        image_data_uri: Base64 data URI string of the image
        crop_box: Dictionary with 'x', 'y', 'width', 'height' keys
    
    Returns:
        PIL Image object of the cropped region, or None if error
    """
    try:
        # Convert Base64 to PIL Image
        img_bytes = decode_frontend_image(image_data_uri)
        if not img_bytes:
            return None
            
        full_image = Image.open(io.BytesIO(img_bytes))
        
        # Crop the image based on user selection
        x = int(crop_box['x'])
        y = int(crop_box['y'])
        w = int(crop_box['width'])
        h = int(crop_box['height'])
        
        cropped_img = full_image.crop((x, y, x + w, y + h))
        return cropped_img
        
    except Exception:
        logger.exception("Image cropping error")
        return None

