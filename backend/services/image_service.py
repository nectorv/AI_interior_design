"""Image processing service for handling image operations."""
import io
import logging
from PIL import Image, ImageOps
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
        img_bytes = decode_frontend_image(image_data_uri)
        if not img_bytes:
            return None
            
        with Image.open(io.BytesIO(img_bytes)) as full_image:
            x, y = int(crop_box['x']), int(crop_box['y'])
            w, h = int(crop_box['width']), int(crop_box['height'])
            
            cropped_img = full_image.crop((x, y, x + w, y + h))
            #Letterboxing to 224x224 for model input
            return ImageOps.pad(cropped_img, (224, 224), method=Image.Resampling.LANCZOS, color=(255, 255, 255))
        
    except Exception:
        logger.exception("Image cropping error")
        return None

