"""Tests for AI service."""
import pytest
import io
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
from backend.services.ai_service import GeminiService
from google.genai import types


def generate_image_bytes(fmt='PNG'):
    """Helper to generate test image bytes."""
    img = Image.new('RGB', (10, 10), color='blue')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format=fmt)
    return img_byte_arr.getvalue()


@pytest.fixture
def mock_config():
    """Mock configuration."""
    with patch('backend.services.ai_service.Config') as mock_cfg:
        mock_cfg.GOOGLE_API_KEY = 'test-api-key'
        mock_cfg.GEMINI_MODEL = 'gemini-2.0-flash-exp'
        mock_cfg.validate = Mock()
        yield mock_cfg


@pytest.fixture
def mock_genai_client():
    """Mock genai client."""
    with patch('backend.services.ai_service.genai.Client') as mock_client:
        yield mock_client


class TestGeminiServiceInit:
    """Tests for GeminiService initialization."""
    
    def test_init_validates_config(self, mock_config, mock_genai_client):
        """Test that initialization validates configuration."""
        # Act
        service = GeminiService()
        
        # Assert
        mock_config.validate.assert_called_once()
    
    def test_init_creates_client_with_api_key(self, mock_config, mock_genai_client):
        """Test that initialization creates client with API key."""
        # Act
        service = GeminiService()
        
        # Assert
        mock_genai_client.assert_called_once_with(api_key='test-api-key')
    
    def test_init_sets_model(self, mock_config, mock_genai_client):
        """Test that initialization sets the model."""
        # Act
        service = GeminiService()
        
        # Assert
        assert service.model == 'gemini-2.0-flash-exp'


class TestGeminiServiceGenerateImage:
    """Tests for GeminiService.generate_image method."""
    
    def test_generate_image_success(self, mock_config, mock_genai_client):
        """Test successful image generation."""
        # Arrange
        service = GeminiService()
        input_bytes = generate_image_bytes('PNG')
        prompt = "Transform this room into modern style"
        output_bytes = generate_image_bytes('JPEG')
        
        # Mock the response
        mock_part = Mock()
        mock_part.inline_data = Mock()
        mock_part.inline_data.data = output_bytes
        
        mock_candidate = Mock()
        mock_candidate.content.parts = [mock_part]
        
        mock_response = Mock()
        mock_response.candidates = [mock_candidate]
        
        service.client.models.generate_content = Mock(return_value=mock_response)
        
        # Act
        result = service.generate_image(input_bytes, prompt)
        
        # Assert
        assert result == output_bytes
        service.client.models.generate_content.assert_called_once()
    
    def test_generate_image_with_different_formats(self, mock_config, mock_genai_client):
        """Test image generation with different image formats."""
        # Arrange
        service = GeminiService()
        
        for fmt, expected_mime in [('PNG', 'image/png'), ('JPEG', 'image/jpeg'), ('WEBP', 'image/webp')]:
            input_bytes = generate_image_bytes(fmt)
            prompt = "Test prompt"
            output_bytes = generate_image_bytes()
            
            # Mock the response
            mock_part = Mock()
            mock_part.inline_data = Mock()
            mock_part.inline_data.data = output_bytes
            
            mock_candidate = Mock()
            mock_candidate.content.parts = [mock_part]
            
            mock_response = Mock()
            mock_response.candidates = [mock_candidate]
            
            service.client.models.generate_content = Mock(return_value=mock_response)
            
            # Act
            result = service.generate_image(input_bytes, prompt)
            
            # Assert
            assert result == output_bytes
            
            # Verify the correct mime type was detected and used
            call_args = service.client.models.generate_content.call_args
            assert call_args is not None
    
    def test_generate_image_calls_api_with_correct_params(self, mock_config, mock_genai_client):
        """Test that API is called with correct parameters."""
        # Arrange
        service = GeminiService()
        input_bytes = generate_image_bytes('PNG')
        prompt = "Transform this room"
        
        mock_part = Mock()
        mock_part.inline_data = Mock()
        mock_part.inline_data.data = b'result'
        
        mock_candidate = Mock()
        mock_candidate.content.parts = [mock_part]
        
        mock_response = Mock()
        mock_response.candidates = [mock_candidate]
        
        service.client.models.generate_content = Mock(return_value=mock_response)
        
        # Act
        result = service.generate_image(input_bytes, prompt)
        
        # Assert
        call_args = service.client.models.generate_content.call_args
        assert call_args[1]['model'] == 'gemini-2.0-flash-exp'
        assert len(call_args[1]['contents']) == 2
        assert call_args[1]['contents'][0] == prompt
        assert isinstance(call_args[1]['config'], types.GenerateContentConfig)
    
    def test_generate_image_no_inline_data(self, mock_config, mock_genai_client):
        """Test when response has no inline data."""
        # Arrange
        service = GeminiService()
        input_bytes = generate_image_bytes()
        prompt = "Test prompt"
        
        # Mock response with no inline data
        mock_part = Mock()
        mock_part.inline_data = None
        
        mock_candidate = Mock()
        mock_candidate.content.parts = [mock_part]
        
        mock_response = Mock()
        mock_response.candidates = [mock_candidate]
        
        service.client.models.generate_content = Mock(return_value=mock_response)
        
        # Act
        result = service.generate_image(input_bytes, prompt)
        
        # Assert
        assert result is None
    
    def test_generate_image_empty_parts(self, mock_config, mock_genai_client):
        """Test when response has no parts."""
        # Arrange
        service = GeminiService()
        input_bytes = generate_image_bytes()
        prompt = "Test prompt"
        
        # Mock response with empty parts
        mock_candidate = Mock()
        mock_candidate.content.parts = []
        
        mock_response = Mock()
        mock_response.candidates = [mock_candidate]
        
        service.client.models.generate_content = Mock(return_value=mock_response)
        
        # Act
        result = service.generate_image(input_bytes, prompt)
        
        # Assert
        assert result is None
    
    def test_generate_image_api_exception(self, mock_config, mock_genai_client):
        """Test handling of API exceptions."""
        # Arrange
        service = GeminiService()
        input_bytes = generate_image_bytes()
        prompt = "Test prompt"
        
        service.client.models.generate_content = Mock(side_effect=Exception("API Error"))
        
        # Act
        result = service.generate_image(input_bytes, prompt)
        
        # Assert
        assert result is None
    
    def test_generate_image_with_empty_prompt(self, mock_config, mock_genai_client):
        """Test image generation with empty prompt."""
        # Arrange
        service = GeminiService()
        input_bytes = generate_image_bytes()
        prompt = ""
        output_bytes = generate_image_bytes()
        
        mock_part = Mock()
        mock_part.inline_data = Mock()
        mock_part.inline_data.data = output_bytes
        
        mock_candidate = Mock()
        mock_candidate.content.parts = [mock_part]
        
        mock_response = Mock()
        mock_response.candidates = [mock_candidate]
        
        service.client.models.generate_content = Mock(return_value=mock_response)
        
        # Act
        result = service.generate_image(input_bytes, prompt)
        
        # Assert
        assert result == output_bytes
    
    def test_generate_image_with_long_prompt(self, mock_config, mock_genai_client):
        """Test image generation with a long prompt."""
        # Arrange
        service = GeminiService()
        input_bytes = generate_image_bytes()
        prompt = "Transform this room " * 100  # Long prompt
        output_bytes = generate_image_bytes()
        
        mock_part = Mock()
        mock_part.inline_data = Mock()
        mock_part.inline_data.data = output_bytes
        
        mock_candidate = Mock()
        mock_candidate.content.parts = [mock_part]
        
        mock_response = Mock()
        mock_response.candidates = [mock_candidate]
        
        service.client.models.generate_content = Mock(return_value=mock_response)
        
        # Act
        result = service.generate_image(input_bytes, prompt)
        
        # Assert
        assert result == output_bytes
    
    def test_generate_image_response_with_multiple_parts(self, mock_config, mock_genai_client):
        """Test when response has multiple parts, returns first with inline data."""
        # Arrange
        service = GeminiService()
        input_bytes = generate_image_bytes()
        prompt = "Test prompt"
        output_bytes = generate_image_bytes()
        
        # Mock response with multiple parts
        mock_part1 = Mock()
        mock_part1.inline_data = None
        
        mock_part2 = Mock()
        mock_part2.inline_data = Mock()
        mock_part2.inline_data.data = output_bytes
        
        mock_candidate = Mock()
        mock_candidate.content.parts = [mock_part1, mock_part2]
        
        mock_response = Mock()
        mock_response.candidates = [mock_candidate]
        
        service.client.models.generate_content = Mock(return_value=mock_response)
        
        # Act
        result = service.generate_image(input_bytes, prompt)
        
        # Assert
        assert result == output_bytes
    
    def test_generate_image_attribute_error(self, mock_config, mock_genai_client):
        """Test handling of attribute errors in response parsing."""
        # Arrange
        service = GeminiService()
        input_bytes = generate_image_bytes()
        prompt = "Test prompt"
        
        # Mock response that will raise AttributeError
        mock_response = Mock()
        mock_response.candidates = None
        
        service.client.models.generate_content = Mock(return_value=mock_response)
        
        # Act
        result = service.generate_image(input_bytes, prompt)
        
        # Assert
        assert result is None
