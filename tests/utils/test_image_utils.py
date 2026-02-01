"""Tests for image utilities."""
import pytest
import io
import base64
from PIL import Image
from backend.utils.image_utils import (
    detect_image_mime_type,
    process_image_for_frontend,
    decode_frontend_image
)

def generate_image_bytes(fmt):
    img = Image.new('RGB', (10, 10), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format=fmt)
    return img_byte_arr.getvalue()

@pytest.mark.parametrize("image_format, expected_mime", [
    ('JPEG', 'image/jpeg'),
    ('PNG', 'image/png'),
    ('WEBP', 'image/webp'),
    ('GIF', 'image/gif'),
])

def test_detect_image_mime_type(image_format, expected_mime):

    #Arrange
    image_bytes = generate_image_bytes(image_format)

    #Act
    result = detect_image_mime_type(image_bytes)

    #Assert
    assert result == expected_mime

@pytest.mark.parametrize("invalid_bytes, expected_mime", [
    (None, "image/png"),
    (b'', "image/png"),
    (b'notanimage', "image/png"),    
])

def test_detect_image_mime_type_invalid(invalid_bytes, expected_mime):

    #Act
    result = detect_image_mime_type(invalid_bytes)

    #Assert
    assert result == expected_mime


@pytest.mark.parametrize("image_format, expected_mime", [
    ('JPEG', 'image/jpeg'),
    ('PNG', 'image/png'),
    ('WEBP', 'image/webp'),
    ('GIF', 'image/gif'),
])

def test_process_image_for_frontend(image_format, expected_mime):

    #Arrange
    image_bytes = generate_image_bytes(image_format)

    #Act
    result = process_image_for_frontend(image_bytes)

    #Assert
    assert result is not None
    assert result.startswith(f'data:{expected_mime};base64,')
    
    # Verify we can decode it back
    base64_part = result.split(',', 1)[1]
    decoded = base64.b64decode(base64_part)
    assert decoded == image_bytes


def test_process_image_for_frontend_none():

    #Act
    result = process_image_for_frontend(None)

    #Assert
    assert result is None


def test_process_image_for_frontend_empty():

    #Act
    result = process_image_for_frontend(b'')

    #Assert
    assert result is None


@pytest.mark.parametrize("image_format", ['JPEG', 'PNG', 'WEBP', 'GIF'])

def test_decode_frontend_image(image_format):

    #Arrange
    image_bytes = generate_image_bytes(image_format)
    data_uri = process_image_for_frontend(image_bytes)

    #Act
    result = decode_frontend_image(data_uri)

    #Assert
    assert result == image_bytes


def test_decode_frontend_image_none():

    #Act
    result = decode_frontend_image(None)

    #Assert
    assert result is None


def test_decode_frontend_image_empty():

    #Act
    result = decode_frontend_image('')

    #Assert
    assert result is None


def test_decode_frontend_image_invalid():

    result = decode_frontend_image('data:image/png;base64,')

    #Assert
    assert result == b''  # Empty base64 string decodes to empty bytes


def test_decode_frontend_image_malformed_base64():

    #Act
    result = decode_frontend_image('data:image/png;base64,!!!invalid!!!')

    #Assert
    assert result is None


def test_roundtrip_encode_decode():
    """Test that encoding and then decoding returns the original bytes."""
    
    #Arrange
    original_bytes = generate_image_bytes('PNG')
    
    #Act
    encoded = process_image_for_frontend(original_bytes)
    decoded = decode_frontend_image(encoded)
    
    #Assert
    assert decoded == original_bytes

