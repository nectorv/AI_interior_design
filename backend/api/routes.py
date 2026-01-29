"""Flask API routes for the interior designer application."""
import logging
from flask import Blueprint, current_app, request, jsonify, render_template

from backend.services.image_service import crop_image_from_data_uri
from backend.utils.image_utils import process_image_for_frontend, decode_frontend_image, detect_image_mime_type
from backend.core.prompts import get_design_prompt, get_refine_prompt, get_empty_room_prompt

logger = logging.getLogger(__name__)

# Create Blueprint
api_bp = Blueprint('api', __name__)


def _get_services():
    """Retrieve shared service instances from the Flask app."""
    ai_service = current_app.extensions.get('ai_service')
    search_service = current_app.extensions.get('search_service')
    if not ai_service or not search_service:
        raise RuntimeError("Services not initialized on the application")
    return ai_service, search_service


@api_bp.route('/')
def index():
    """Render the main application page."""
    return render_template('index.html', default_style="Nordic", default_room="Living Room")


@api_bp.route('/api/redesign', methods=['POST'])
def redesign_image():
    """Endpoint for redesigning a room image.
    
    Expects:
        - file: Image file in request.files
        - style: Design style (form data)
        - room_type: Type of room (form data)
        - empty_then_generate: Optional boolean flag (form data, default: False)
    
    Returns:
        JSON with original_image, empty_image, and final_image (data URIs)
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    original_bytes = file.read()
    if not original_bytes:
        return jsonify({'error': 'Empty file'}), 400

    # Validate file content by detecting actual image format
    # This is more reliable than trusting the mimetype from the client
    allowed_mimetypes = {'image/jpeg', 'image/png', 'image/webp'}
    detected_mime_type = detect_image_mime_type(original_bytes)
    
    if detected_mime_type not in allowed_mimetypes:
        return jsonify({'error': f'Unsupported file type. Detected: {detected_mime_type}. Supported: JPEG, PNG, WebP'}), 400

    style = (request.form.get('style') or 'Nordic').strip()
    room_type = (request.form.get('room_type') or 'Living Room').strip()
    additional_instructions = request.form.get('additional_instructions', '').strip()
    
    # Check if empty_then_generate flag is set
    empty_then_generate = request.form.get('empty_then_generate', 'false').lower() in ('true', '1', 'yes')

    ai_service, _ = _get_services()

    try:
        if empty_then_generate:
            # Step 1: Empty the room
            empty_prompt = get_empty_room_prompt()
            empty_bytes = ai_service.generate_image(original_bytes, empty_prompt)
            
            if not empty_bytes:
                return jsonify({'error': 'Failed to empty room'}), 500
            
            # Step 2: Generate design from empty room
            design_prompt = get_design_prompt(style, room_type, additional_instructions)
            final_bytes = ai_service.generate_image(empty_bytes, design_prompt)
            
            if not final_bytes:
                return jsonify({'error': 'Failed to design room'}), 500
            
            return jsonify({
                'original_image': process_image_for_frontend(original_bytes),
                'empty_image': process_image_for_frontend(empty_bytes),
                'final_image': process_image_for_frontend(final_bytes)
            })
        else:
            # Original single-step process
            design_prompt = get_design_prompt(style, room_type, additional_instructions)
            final_bytes = ai_service.generate_image(original_bytes, design_prompt)
            
            if not final_bytes:
                return jsonify({'error': 'Failed to design room'}), 500
            
            return jsonify({
                'original_image': process_image_for_frontend(original_bytes),
                'empty_image': process_image_for_frontend(original_bytes),  # Keep original for comparison
                'final_image': process_image_for_frontend(final_bytes)
            })
    except Exception:
        logger.exception("Failed to generate design")
        return jsonify({'error': 'Failed to design room'}), 500


@api_bp.route('/api/refine', methods=['POST'])
def refine_image():
    """Endpoint for refining an existing design.
    
    Expects JSON:
        - image_data: Base64 data URI of the image
        - prompt: Refinement instruction
    
    Returns:
        JSON with refined_image (data URI)
    """
    data = request.get_json(silent=True) or {}
    image_data = data.get('image_data')
    prompt_text = (data.get('prompt') or '').strip()

    if not image_data:
        return jsonify({'error': 'Missing image data'}), 400

    if not prompt_text:
        return jsonify({'error': 'Missing prompt'}), 400

    input_bytes = decode_frontend_image(image_data)
    if not input_bytes:
        return jsonify({'error': 'Invalid image'}), 400

    ai_service, _ = _get_services()

    try:
        prompt = get_refine_prompt(prompt_text)
        refined_bytes = ai_service.generate_image(input_bytes, prompt)
    except Exception:
        logger.exception("Failed to refine design")
        return jsonify({'error': 'Failed to refine'}), 500

    if not refined_bytes:
        return jsonify({'error': 'Failed to refine'}), 500

    return jsonify({
        'refined_image': process_image_for_frontend(refined_bytes)
    })


@api_bp.route('/api/search-furniture', methods=['POST'])
def search_furniture():
    """Endpoint for searching furniture based on image crop.
    
    Expects multipart/form-data:
        - image: Image file to search within
        - box_x, box_y, box_width, box_height: Crop region coordinates
    
    Returns:
        JSON with results array containing matching furniture items
    """
    # Validate image file
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    file = request.files['image']
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Validate crop box parameters
    try:
        box_x = float(request.form.get('box_x', 0))
        box_y = float(request.form.get('box_y', 0))
        box_width = float(request.form.get('box_width'))
        box_height = float(request.form.get('box_height'))
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid crop box values'}), 400

    if box_width <= 0 or box_height <= 0:
        return jsonify({'error': 'Crop dimensions must be positive'}), 400

    try:
        # Read image file bytes
        image_bytes = file.read()
        if not image_bytes:
            return jsonify({'error': 'Empty file'}), 400

        # Validate file content by detecting actual image format
        detected_mime_type = detect_image_mime_type(image_bytes)
        allowed_mimetypes = {'image/jpeg', 'image/png', 'image/webp'}
        
        if detected_mime_type not in allowed_mimetypes:
            return jsonify({'error': f'Unsupported file type. Detected: {detected_mime_type}. Supported: JPEG, PNG, WebP'}), 400

        # Crop the image based on user selection
        from PIL import Image as PILImage
        import io
        from PIL import ImageOps
        
        with PILImage.open(io.BytesIO(image_bytes)) as full_image:
            crop_region = (
                int(box_x),
                int(box_y),
                int(box_x + box_width),
                int(box_y + box_height)
            )
            cropped_img = full_image.crop(crop_region)
            # Letterboxing to 224x224 for model input
            cropped_img = ImageOps.pad(cropped_img, (224, 224), method=PILImage.Resampling.LANCZOS, color=(255, 255, 255))

        if not cropped_img:
            return jsonify({'error': 'Failed to process image'}), 400

        # Search for similar furniture
        _, search_service = _get_services()
        try:
            results = search_service.search(cropped_img, top_k=4)
        except RuntimeError as e:
            # Known condition when embeddings or dataset are not loaded
            logger.warning("Search unavailable: %s", str(e))
            return jsonify({'error': 'Search unavailable: embeddings or dataset not loaded'}), 503

        return jsonify({'results': results})

    except Exception:
        logger.exception("Search error")
        return jsonify({'error': 'Failed to search furniture'}), 500

