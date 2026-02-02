"""Tests for Qdrant service."""
import pytest
import io
from unittest.mock import Mock, patch, MagicMock
from PIL import Image


def generate_pil_image():
    """Helper to generate a PIL Image."""
    return Image.new('RGB', (224, 224), color='green')


@pytest.fixture
def mock_config():
    """Mock configuration."""
    with patch('backend.services.qdrant_service.Config') as mock_cfg:
        mock_cfg.QDRANT_URL = 'https://test-qdrant-url.example.com'
        mock_cfg.QDRANT_API_KEY = 'test-api-key'
        mock_cfg.QDRANT_COLLECTION_NAME = 'test-collection'
        yield mock_cfg


@pytest.fixture
def mock_clip_service():
    """Mock CLIP service."""
    with patch('backend.services.qdrant_service.LambdaCLIPService') as mock_clip_class:
        mock_clip = Mock()
        mock_clip.get_image_embedding.return_value = [0.1] * 512
        mock_clip_class.return_value = mock_clip
        yield mock_clip


class TestQdrantServiceInit:
    """Tests for QdrantService initialization."""
    
    def test_init_without_qdrant_url(self, mock_clip_service):
        """Test initialization fails without QDRANT_URL."""
        # Arrange
        with patch('backend.services.qdrant_service.Config') as mock_cfg:
            mock_cfg.QDRANT_URL = None
            mock_cfg.QDRANT_API_KEY = 'test-key'
            mock_cfg.QDRANT_COLLECTION_NAME = 'test-collection'
            
            from backend.services.qdrant_service import QdrantService
            
            # Act
            service = QdrantService()
            
            # Assert
            assert service.is_initialized is False
            assert service.qdrant_client is None
    
    def test_init_without_api_key(self, mock_clip_service):
        """Test initialization fails without API key."""
        # Arrange
        with patch('backend.services.qdrant_service.Config') as mock_cfg:
            mock_cfg.QDRANT_URL = 'https://test.com'
            mock_cfg.QDRANT_API_KEY = None
            mock_cfg.QDRANT_COLLECTION_NAME = 'test-collection'
            
            from backend.services.qdrant_service import QdrantService
            
            # Act
            service = QdrantService()
            
            # Assert
            assert service.is_initialized is False


class TestQdrantServiceSearch:
    """Tests for QdrantService.search method."""
    
    def test_search_not_initialized_raises_error(self, mock_config, mock_clip_service):
        """Test search raises error when service not initialized."""
        # Arrange
        from backend.services.qdrant_service import QdrantService
        
        with patch('backend.services.qdrant_service.Config') as mock_cfg:
            mock_cfg.QDRANT_URL = None
            service = QdrantService()
            img = generate_pil_image()
            
            # Act & Assert
            with pytest.raises(RuntimeError, match="Qdrant search service not initialized"):
                service.search(img)
    
    def test_search_clip_service_none_raises_error(self, mock_config):
        """Test search raises error when CLIP service is None."""
        # Arrange - create service with mocked Qdrant but no CLIP
        from backend.services.qdrant_service import QdrantService
        
        with patch('backend.services.qdrant_service.LambdaCLIPService') as mock_clip_class:
            # Make CLIP service return None
            mock_clip_class.return_value = None
            
            # Mock Qdrant to avoid actual initialization
            with patch('backend.services.qdrant_service.Config') as mock_cfg:
                mock_cfg.QDRANT_URL = None
                service = QdrantService()
                service.is_initialized = True  # Force it to be initialized
                service.qdrant_client = Mock()  # Add a mock client
                service.clip_service = None  # But no CLIP service
                
                img = generate_pil_image()
                
                # Act & Assert
                with pytest.raises(RuntimeError, match="CLIP service not initialized"):
                    service.search(img)
    
    def test_search_returns_empty_on_exception(self, mock_config, mock_clip_service):
        """Test search returns empty list on exception."""
        # Arrange
        from backend.services.qdrant_service import QdrantService
        
        with patch('backend.services.qdrant_service.Config') as mock_cfg:
            mock_cfg.QDRANT_URL = None
            service = QdrantService()
            service.is_initialized = True
            service.qdrant_client = Mock()
            service.qdrant_client.query_points.side_effect = Exception("Search failed")
            
            img = generate_pil_image()
            
            # Act
            results = service.search(img)
            
            # Assert
            assert results == []
