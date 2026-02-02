"""Tests for CLIP service."""
import pytest
import io
import time
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
from backend.services.clip_service import LambdaCLIPService


def generate_image_bytes(fmt='JPEG'):
    """Helper to generate test image bytes."""
    img = Image.new('RGB', (10, 10), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format=fmt)
    return img_byte_arr.getvalue()


def generate_pil_image():
    """Helper to generate a PIL Image."""
    return Image.new('RGB', (10, 10), color='blue')


@pytest.fixture
def mock_config():
    """Mock configuration."""
    with patch('backend.services.clip_service.Config') as mock_cfg:
        mock_cfg.LAMBDA_CLIP_URL = 'https://test-lambda-url.example.com'
        yield mock_cfg


@pytest.fixture
def mock_requests():
    """Mock requests module."""
    with patch('backend.services.clip_service.requests') as mock_req:
        yield mock_req


class TestLambdaCLIPServiceInit:
    """Tests for LambdaCLIPService initialization."""
    
    def test_init_with_default_url(self, mock_config):
        """Test initialization with default URL from config."""
        # Act
        service = LambdaCLIPService()
        
        # Assert
        assert service.url == 'https://test-lambda-url.example.com'
        assert service.timeout == 30
    
    def test_init_with_custom_url(self):
        """Test initialization with custom URL."""
        # Act
        service = LambdaCLIPService(url='https://custom-url.com', timeout=60)
        
        # Assert
        assert service.url == 'https://custom-url.com'
        assert service.timeout == 60
    
    def test_init_without_url(self):
        """Test initialization without URL logs warning."""
        # Arrange
        with patch('backend.services.clip_service.Config') as mock_cfg:
            mock_cfg.LAMBDA_CLIP_URL = None
            
            # Act
            service = LambdaCLIPService()
            
            # Assert
            assert service.url is None
    
    def test_init_sets_warm_interval(self, mock_config):
        """Test that initialization sets warm interval."""
        # Act
        service = LambdaCLIPService()
        
        # Assert
        assert service._warm_interval == 20
        assert service._last_warm == 0.0


class TestLambdaCLIPServiceImageToBytes:
    """Tests for _image_to_bytes method."""
    
    def test_image_to_bytes_converts_rgb(self, mock_config):
        """Test that PIL image is converted to RGB JPEG bytes."""
        # Arrange
        service = LambdaCLIPService()
        img = Image.new('RGBA', (10, 10), color=(255, 0, 0, 128))
        
        # Act
        result = service._image_to_bytes(img)
        
        # Assert
        assert isinstance(result, bytes)
        assert len(result) > 0
        
        # Verify it's a valid JPEG
        reloaded = Image.open(io.BytesIO(result))
        assert reloaded.format == 'JPEG'
        assert reloaded.mode == 'RGB'


class TestLambdaCLIPServiceGetImageEmbedding:
    """Tests for get_image_embedding method."""
    
    def test_get_image_embedding_with_pil_image(self, mock_config, mock_requests):
        """Test getting embedding from PIL Image."""
        # Arrange
        service = LambdaCLIPService()
        img = generate_pil_image()
        expected_embedding = [0.1] * 512
        
        mock_response = Mock()
        mock_response.json.return_value = {'embedding': expected_embedding}
        mock_requests.post.return_value = mock_response
        
        # Act
        result = service.get_image_embedding(img)
        
        # Assert
        assert result == expected_embedding
        mock_requests.post.assert_called_once()
        call_args = mock_requests.post.call_args
        assert call_args[0][0] == service.url
        assert call_args[1]['headers'] == {'Content-Type': 'application/octet-stream'}
    
    def test_get_image_embedding_with_file_path(self, mock_config, mock_requests, tmp_path):
        """Test getting embedding from file path."""
        # Arrange
        service = LambdaCLIPService()
        image_path = tmp_path / "test.jpg"
        img = generate_pil_image()
        img.save(image_path)
        
        expected_embedding = [0.2] * 512
        mock_response = Mock()
        mock_response.json.return_value = {'embedding': expected_embedding}
        mock_requests.post.return_value = mock_response
        
        # Act
        result = service.get_image_embedding(str(image_path))
        
        # Assert
        assert result == expected_embedding
    
    def test_get_image_embedding_raises_if_no_url(self, mock_config):
        """Test that method raises ValueError if URL not configured."""
        # Arrange
        service = LambdaCLIPService()
        service.url = None
        img = generate_pil_image()
        
        # Act & Assert
        with pytest.raises(ValueError, match="Lambda CLIP URL not configured"):
            service.get_image_embedding(img)
    
    def test_get_image_embedding_unsupported_type(self, mock_config):
        """Test that unsupported input type raises ValueError."""
        # Arrange
        service = LambdaCLIPService()
        
        # Act & Assert
        with pytest.raises(ValueError, match="Unsupported image_input type"):
            service.get_image_embedding(12345)
    
    def test_get_image_embedding_unwraps_nested_list(self, mock_config, mock_requests):
        """Test that nested embedding list is unwrapped."""
        # Arrange
        service = LambdaCLIPService()
        img = generate_pil_image()
        nested_embedding = [[0.3] * 512]  # Nested list
        
        mock_response = Mock()
        mock_response.json.return_value = {'embedding': nested_embedding}
        mock_requests.post.return_value = mock_response
        
        # Act
        result = service.get_image_embedding(img)
        
        # Assert
        assert result == [0.3] * 512
        assert isinstance(result, list)
    
    def test_get_image_embedding_validates_length(self, mock_config):
        """Test that wrong embedding length raises ValueError."""
        # Arrange
        service = LambdaCLIPService()
        img = generate_pil_image()
        wrong_embedding = [0.1] * 256  # Wrong length
        
        with patch('backend.services.clip_service.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {'embedding': wrong_embedding}
            mock_post.return_value = mock_response
            
            # Act & Assert
            with pytest.raises(ValueError, match="Embedding shape unexpected"):
                service.get_image_embedding(img)
    
    def test_get_image_embedding_validates_response_format(self, mock_config):
        """Test that invalid response format raises ValueError."""
        # Arrange
        service = LambdaCLIPService()
        img = generate_pil_image()
        
        with patch('backend.services.clip_service.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {'wrong_key': [0.1] * 512}
            mock_post.return_value = mock_response
            
            # Act & Assert
            with pytest.raises(ValueError, match="Unexpected response from Lambda"):
                service.get_image_embedding(img)
    
    def test_get_image_embedding_handles_http_error(self, mock_config):
        """Test that HTTP errors are raised."""
        # Arrange
        import requests as real_requests
        service = LambdaCLIPService()
        img = generate_pil_image()
        
        with patch('backend.services.clip_service.requests.post') as mock_post:
            mock_post.side_effect = real_requests.RequestException("Connection error")
            
            # Act & Assert
            with pytest.raises(real_requests.RequestException):
                service.get_image_embedding(img)
    
    def test_get_image_embedding_converts_to_float(self, mock_config, mock_requests):
        """Test that embedding values are converted to float."""
        # Arrange
        service = LambdaCLIPService()
        img = generate_pil_image()
        int_embedding = [1] * 512  # Integer values
        
        mock_response = Mock()
        mock_response.json.return_value = {'embedding': int_embedding}
        mock_requests.post.return_value = mock_response
        
        # Act
        result = service.get_image_embedding(img)
        
        # Assert
        assert all(isinstance(x, float) for x in result)


class TestLambdaCLIPServiceWarmAsync:
    """Tests for warm_async method."""
    
    def test_warm_async_sends_request(self, mock_config, mock_requests):
        """Test that warm_async sends a warming request."""
        # Arrange
        service = LambdaCLIPService()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.post.return_value = mock_response
        
        # Act
        result = service.warm_async(force=True)
        
        # Assert
        assert result is True
        # Give thread time to execute
        time.sleep(0.1)
    
    def test_warm_async_respects_interval(self, mock_config, mock_requests):
        """Test that warm_async respects the warm interval."""
        # Arrange
        service = LambdaCLIPService()
        service._last_warm = time.time()
        
        # Act
        result = service.warm_async(force=False)
        
        # Assert
        assert result is False
    
    def test_warm_async_force_bypasses_interval(self, mock_config, mock_requests):
        """Test that force=True bypasses the interval check."""
        # Arrange
        service = LambdaCLIPService()
        service._last_warm = time.time()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.post.return_value = mock_response
        
        # Act
        result = service.warm_async(force=True)
        
        # Assert
        assert result is True
    
    def test_warm_async_handles_exceptions(self, mock_config, mock_requests):
        """Test that warm_async handles exceptions gracefully."""
        # Arrange
        service = LambdaCLIPService()
        mock_requests.post.side_effect = Exception("Network error")
        
        # Act
        result = service.warm_async(force=True)
        
        # Assert
        assert result is True  # Still returns True as request was scheduled
        # Give thread time to execute
        time.sleep(0.1)
