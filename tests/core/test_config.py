"""Tests for backend.core.config module."""
import os
import pytest
from unittest.mock import patch
from backend.core.config import Config


class TestConfigAttributes:
    """Test Config class attributes."""
    
    def test_config_has_google_api_key_attribute(self):
        """Test that Config has GOOGLE_API_KEY attribute."""
        assert hasattr(Config, 'GOOGLE_API_KEY')
    
    def test_config_has_lambda_clip_url_attribute(self):
        """Test that Config has LAMBDA_CLIP_URL attribute."""
        assert hasattr(Config, 'LAMBDA_CLIP_URL')
    
    def test_config_has_max_content_length_attribute(self):
        """Test that Config has MAX_CONTENT_LENGTH attribute."""
        assert hasattr(Config, 'MAX_CONTENT_LENGTH')
    
    def test_config_has_qdrant_url_attribute(self):
        """Test that Config has QDRANT_URL attribute."""
        assert hasattr(Config, 'QDRANT_URL')
    
    def test_config_has_qdrant_api_key_attribute(self):
        """Test that Config has QDRANT_API_KEY attribute."""
        assert hasattr(Config, 'QDRANT_API_KEY')
    
    def test_config_has_qdrant_collection_name_attribute(self):
        """Test that Config has QDRANT_COLLECTION_NAME attribute."""
        assert hasattr(Config, 'QDRANT_COLLECTION_NAME')
    
    def test_config_has_model_id_attribute(self):
        """Test that Config has MODEL_ID attribute."""
        assert hasattr(Config, 'MODEL_ID')
    
    def test_config_has_gemini_model_attribute(self):
        """Test that Config has GEMINI_MODEL attribute."""
        assert hasattr(Config, 'GEMINI_MODEL')


class TestConfigValues:
    """Test Config class default values."""
    
    def test_max_content_length_is_16mb(self):
        """Test that MAX_CONTENT_LENGTH is set to 16MB."""
        assert Config.MAX_CONTENT_LENGTH == 16 * 1024 * 1024
    
    def test_qdrant_collection_name_is_furniture_items(self):
        """Test that QDRANT_COLLECTION_NAME is 'furniture_items'."""
        assert Config.QDRANT_COLLECTION_NAME == "furniture_items"
    
    def test_model_id_is_clip_vit_base(self):
        """Test that MODEL_ID is set correctly."""
        assert Config.MODEL_ID == "openai/clip-vit-base-patch32"
    
    def test_gemini_model_is_flash_image(self):
        """Test that GEMINI_MODEL is set correctly."""
        assert Config.GEMINI_MODEL == "gemini-2.5-flash-image"


class TestConfigValidate:
    """Test Config.validate() method."""
    
    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_key'})
    def test_validate_with_google_api_key(self):
        """Test validate passes when GOOGLE_API_KEY is present."""
        # Reload config to pick up environment variable
        from importlib import reload
        from backend.core import config
        reload(config)
        
        # Should not raise
        config.Config.validate()
    
    @patch.dict(os.environ, {}, clear=True)
    def test_validate_without_google_api_key_raises_error(self):
        """Test validate raises ValueError when GOOGLE_API_KEY is missing."""
        # Reload config to pick up environment variable
        from importlib import reload
        from backend.core import config
        reload(config)
        
        with pytest.raises(ValueError, match="GOOGLE_API_KEY not found"):
            config.Config.validate()
    
    @patch.dict(os.environ, {'GOOGLE_API_KEY': ''})
    def test_validate_with_empty_google_api_key_raises_error(self):
        """Test validate raises ValueError when GOOGLE_API_KEY is empty."""
        # Reload config to pick up environment variable
        from importlib import reload
        from backend.core import config
        reload(config)
        
        with pytest.raises(ValueError, match="GOOGLE_API_KEY not found"):
            config.Config.validate()


class TestConfigEnvironmentVariables:
    """Test Config reads environment variables correctly."""
    
    @patch.dict(os.environ, {'LAMBDA_CLIP_URL': 'https://test.lambda.url'})
    def test_lambda_clip_url_from_env(self):
        """Test LAMBDA_CLIP_URL is read from environment."""
        from importlib import reload
        from backend.core import config
        reload(config)
        
        assert config.Config.LAMBDA_CLIP_URL == 'https://test.lambda.url'
    
    @patch.dict(os.environ, {'QDRANT_URL': 'https://test.qdrant.url'})
    def test_qdrant_url_from_env(self):
        """Test QDRANT_URL is read from environment."""
        from importlib import reload
        from backend.core import config
        reload(config)
        
        assert config.Config.QDRANT_URL == 'https://test.qdrant.url'
    
    @patch.dict(os.environ, {'QDRANT_API_KEY': 'test_qdrant_key'})
    def test_qdrant_api_key_from_env(self):
        """Test QDRANT_API_KEY is read from environment."""
        from importlib import reload
        from backend.core import config
        reload(config)
        
        assert config.Config.QDRANT_API_KEY == 'test_qdrant_key'
    
    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_google_key'})
    def test_google_api_key_from_env(self):
        """Test GOOGLE_API_KEY is read from environment."""
        from importlib import reload
        from backend.core import config
        reload(config)
        
        assert config.Config.GOOGLE_API_KEY == 'test_google_key'


class TestConfigClassMethod:
    """Test that validate is a class method."""
    
    def test_validate_is_classmethod(self):
        """Test that validate is accessible as a class method."""
        assert callable(Config.validate)
        assert hasattr(Config.validate, '__self__')
        assert Config.validate.__self__ is Config
