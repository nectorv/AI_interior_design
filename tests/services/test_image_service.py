"""Tests for image service."""
import pytest
import io
from unittest.mock import Mock, patch
from PIL import Image
from backend.services.image_service import crop_image_from_data_uri


def generate_test_data_uri():
    """Helper to generate a test data URI."""
    img = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_bytes = img_byte_arr.getvalue()
    
    import base64
    b64_string = base64.b64encode(img_bytes).decode('utf-8')
    return f'data:image/png;base64,{b64_string}'


class TestCropImageFromDataUri:
    """Tests for crop_image_from_data_uri function."""
    
    def test_crop_image_success(self):
        """Test successful image cropping."""
        # Arrange
        data_uri = generate_test_data_uri()
        crop_box = {'x': 10, 'y': 10, 'width': 50, 'height': 50}
        
        # Act
        result = crop_image_from_data_uri(data_uri, crop_box)
        
        # Assert
        assert result is not None
        assert isinstance(result, Image.Image)
        # Should be letterboxed to 224x224
        assert result.size == (224, 224)
        assert result.mode == 'RGB'
    
    def test_crop_image_with_different_sizes(self):
        """Test cropping with various sizes."""
        # Arrange
        data_uri = generate_test_data_uri()
        test_cases = [
            {'x': 0, 'y': 0, 'width': 20, 'height': 20},
            {'x': 50, 'y': 50, 'width': 40, 'height': 40},
            {'x': 25, 'y': 25, 'width': 30, 'height': 30},
        ]
        
        for crop_box in test_cases:
            # Act
            result = crop_image_from_data_uri(data_uri, crop_box)
            
            # Assert
            assert result is not None
            assert result.size == (224, 224)
    
    def test_crop_image_full_image(self):
        """Test cropping the full image."""
        # Arrange
        data_uri = generate_test_data_uri()
        crop_box = {'x': 0, 'y': 0, 'width': 100, 'height': 100}
        
        # Act
        result = crop_image_from_data_uri(data_uri, crop_box)
        
        # Assert
        assert result is not None
        assert result.size == (224, 224)
    
    def test_crop_image_with_string_coordinates(self):
        """Test that string coordinates are converted to integers."""
        # Arrange
        data_uri = generate_test_data_uri()
        crop_box = {'x': '10', 'y': '10', 'width': '50', 'height': '50'}
        
        # Act
        result = crop_image_from_data_uri(data_uri, crop_box)
        
        # Assert
        assert result is not None
        assert result.size == (224, 224)
    
    def test_crop_image_with_float_coordinates(self):
        """Test that float coordinates are converted to integers."""
        # Arrange
        data_uri = generate_test_data_uri()
        crop_box = {'x': 10.5, 'y': 10.7, 'width': 50.2, 'height': 50.8}
        
        # Act
        result = crop_image_from_data_uri(data_uri, crop_box)
        
        # Assert
        assert result is not None
        assert result.size == (224, 224)
    
    def test_crop_image_invalid_data_uri(self):
        """Test with invalid data URI returns None."""
        # Arrange
        invalid_uri = 'not-a-valid-uri'
        crop_box = {'x': 10, 'y': 10, 'width': 50, 'height': 50}
        
        # Act
        result = crop_image_from_data_uri(invalid_uri, crop_box)
        
        # Assert
        assert result is None
    
    def test_crop_image_none_data_uri(self):
        """Test with None data URI returns None."""
        # Arrange
        crop_box = {'x': 10, 'y': 10, 'width': 50, 'height': 50}
        
        # Act
        result = crop_image_from_data_uri(None, crop_box)
        
        # Assert
        assert result is None
    
    def test_crop_image_empty_data_uri(self):
        """Test with empty data URI returns None."""
        # Arrange
        crop_box = {'x': 10, 'y': 10, 'width': 50, 'height': 50}
        
        # Act
        result = crop_image_from_data_uri('', crop_box)
        
        # Assert
        assert result is None
    
    def test_crop_image_invalid_crop_box(self):
        """Test with invalid crop box returns None."""
        # Arrange
        data_uri = generate_test_data_uri()
        invalid_crop_box = {'x': 'invalid', 'y': 10, 'width': 50, 'height': 50}
        
        # Act
        result = crop_image_from_data_uri(data_uri, invalid_crop_box)
        
        # Assert
        assert result is None
    
    def test_crop_image_missing_crop_box_keys(self):
        """Test with missing crop box keys returns None."""
        # Arrange
        data_uri = generate_test_data_uri()
        incomplete_crop_box = {'x': 10, 'y': 10}  # Missing width and height
        
        # Act
        result = crop_image_from_data_uri(data_uri, incomplete_crop_box)
        
        # Assert
        assert result is None
    
    def test_crop_image_letterboxing_with_non_square_crop(self):
        """Test that non-square crops are letterboxed to 224x224."""
        # Arrange
        data_uri = generate_test_data_uri()
        # Wide crop
        crop_box = {'x': 10, 'y': 40, 'width': 80, 'height': 20}
        
        # Act
        result = crop_image_from_data_uri(data_uri, crop_box)
        
        # Assert
        assert result is not None
        assert result.size == (224, 224)
        # Letterboxing should add white padding
    
    def test_crop_image_with_jpeg_data_uri(self):
        """Test cropping with JPEG data URI."""
        # Arrange
        img = Image.new('RGB', (100, 100), color='blue')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_bytes = img_byte_arr.getvalue()
        
        import base64
        b64_string = base64.b64encode(img_bytes).decode('utf-8')
        data_uri = f'data:image/jpeg;base64,{b64_string}'
        
        crop_box = {'x': 10, 'y': 10, 'width': 50, 'height': 50}
        
        # Act
        result = crop_image_from_data_uri(data_uri, crop_box)
        
        # Assert
        assert result is not None
        assert result.size == (224, 224)
    
    def test_crop_image_boundary_crop(self):
        """Test cropping at image boundaries."""
        # Arrange
        data_uri = generate_test_data_uri()
        # Crop from bottom-right corner
        crop_box = {'x': 80, 'y': 80, 'width': 20, 'height': 20}
        
        # Act
        result = crop_image_from_data_uri(data_uri, crop_box)
        
        # Assert
        assert result is not None
        assert result.size == (224, 224)
    
    @patch('backend.services.image_service.decode_frontend_image')
    def test_crop_image_handles_decode_failure(self, mock_decode):
        """Test handling of decode failures."""
        # Arrange
        mock_decode.return_value = None
        data_uri = 'some-uri'
        crop_box = {'x': 10, 'y': 10, 'width': 50, 'height': 50}
        
        # Act
        result = crop_image_from_data_uri(data_uri, crop_box)
        
        # Assert
        assert result is None
        mock_decode.assert_called_once_with(data_uri)
