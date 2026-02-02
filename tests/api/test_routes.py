"""Tests for API routes."""
import pytest
import io
import base64
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
from flask import Flask
from backend.api.routes import api_bp


def generate_test_image_bytes(fmt='PNG'):
    """Helper to generate test image bytes."""
    img = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format=fmt)
    return img_byte_arr.getvalue()


def generate_test_data_uri():
    """Helper to generate a test data URI."""
    img_bytes = generate_test_image_bytes()
    b64_string = base64.b64encode(img_bytes).decode('utf-8')
    return f'data:image/png;base64,{b64_string}'


@pytest.fixture
def app():
    """Create and configure a test Flask application."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(api_bp)
    
    # Mock services
    mock_ai_service = Mock()
    mock_search_service = Mock()
    
    app.extensions['ai_service'] = mock_ai_service
    app.extensions['search_service'] = mock_search_service
    
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def mock_ai_service(app):
    """Get the mocked AI service."""
    return app.extensions['ai_service']


@pytest.fixture
def mock_search_service(app):
    """Get the mocked search service."""
    return app.extensions['search_service']


class TestIndexRoute:
    """Tests for the index route."""
    
    @patch('backend.api.routes.render_template')
    def test_index_returns_200(self, mock_render, client):
        """Test that index route returns 200."""
        # Arrange
        mock_render.return_value = '<html>Test</html>'
        
        # Act
        response = client.get('/')
        
        # Assert
        assert response.status_code == 200
        mock_render.assert_called_once_with('index.html', default_style="Nordic", default_room="Living Room")
    
    @patch('backend.api.routes.render_template')
    def test_index_renders_template(self, mock_render, client):
        """Test that index route renders the template."""
        # Arrange
        mock_render.return_value = '<html><body>Test Page</body></html>'
        
        # Act
        response = client.get('/')
        
        # Assert
        assert response.status_code == 200
        assert b'Test Page' in response.data


class TestRedesignRoute:
    """Tests for the /api/redesign route."""
    
    def test_redesign_success_simple_mode(self, client, mock_ai_service):
        """Test successful redesign in simple mode."""
        # Arrange
        input_bytes = generate_test_image_bytes()
        output_bytes = generate_test_image_bytes()
        mock_ai_service.generate_image.return_value = output_bytes
        
        data = {
            'file': (io.BytesIO(input_bytes), 'test.png'),
            'style': 'Modern',
            'room_type': 'Bedroom'
        }
        
        # Act
        response = client.post('/api/redesign', data=data, content_type='multipart/form-data')
        
        # Assert
        assert response.status_code == 200
        json_data = response.get_json()
        assert 'original_image' in json_data
        assert 'empty_image' in json_data
        assert 'final_image' in json_data
        assert json_data['original_image'].startswith('data:image/')
        mock_ai_service.generate_image.assert_called_once()
    
    def test_redesign_success_empty_then_generate_mode(self, client, mock_ai_service):
        """Test successful redesign in empty_then_generate mode."""
        # Arrange
        input_bytes = generate_test_image_bytes()
        empty_bytes = generate_test_image_bytes()
        final_bytes = generate_test_image_bytes()
        mock_ai_service.generate_image.side_effect = [empty_bytes, final_bytes]
        
        data = {
            'file': (io.BytesIO(input_bytes), 'test.png'),
            'style': 'Nordic',
            'room_type': 'Living Room',
            'empty_then_generate': 'true'
        }
        
        # Act
        response = client.post('/api/redesign', data=data, content_type='multipart/form-data')
        
        # Assert
        assert response.status_code == 200
        json_data = response.get_json()
        assert 'original_image' in json_data
        assert 'empty_image' in json_data
        assert 'final_image' in json_data
        assert mock_ai_service.generate_image.call_count == 2
    
    def test_redesign_no_file(self, client):
        """Test redesign without file upload."""
        # Act
        response = client.post('/api/redesign', data={}, content_type='multipart/form-data')
        
        # Assert
        assert response.status_code == 400
        assert b'No file uploaded' in response.data
    
    def test_redesign_empty_filename(self, client):
        """Test redesign with empty filename."""
        # Arrange
        data = {
            'file': (io.BytesIO(b''), ''),
        }
        
        # Act
        response = client.post('/api/redesign', data=data, content_type='multipart/form-data')
        
        # Assert
        assert response.status_code == 400
        assert b'No file selected' in response.data
    
    def test_redesign_empty_file_content(self, client):
        """Test redesign with empty file content."""
        # Arrange
        data = {
            'file': (io.BytesIO(b''), 'test.png'),
        }
        
        # Act
        response = client.post('/api/redesign', data=data, content_type='multipart/form-data')
        
        # Assert
        assert response.status_code == 400
        assert b'Empty file' in response.data
    
    def test_redesign_unsupported_file_type(self, client):
        """Test redesign with unsupported file type."""
        # Arrange - Create a GIF file (not supported)
        img = Image.new('RGB', (10, 10), color='blue')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='GIF')
        
        data = {
            'file': (io.BytesIO(img_byte_arr.getvalue()), 'test.gif'),
        }
        
        # Act
        response = client.post('/api/redesign', data=data, content_type='multipart/form-data')
        
        # Assert
        assert response.status_code == 400
        assert b'Unsupported file type' in response.data
    
    def test_redesign_with_additional_instructions(self, client, mock_ai_service):
        """Test redesign with additional instructions."""
        # Arrange
        input_bytes = generate_test_image_bytes()
        output_bytes = generate_test_image_bytes()
        mock_ai_service.generate_image.return_value = output_bytes
        
        data = {
            'file': (io.BytesIO(input_bytes), 'test.png'),
            'style': 'Modern',
            'room_type': 'Office',
            'additional_instructions': 'Add more plants'
        }
        
        # Act
        response = client.post('/api/redesign', data=data, content_type='multipart/form-data')
        
        # Assert
        assert response.status_code == 200
    
    def test_redesign_ai_service_returns_none(self, client, mock_ai_service):
        """Test redesign when AI service returns None."""
        # Arrange
        input_bytes = generate_test_image_bytes()
        mock_ai_service.generate_image.return_value = None
        
        data = {
            'file': (io.BytesIO(input_bytes), 'test.png'),
        }
        
        # Act
        response = client.post('/api/redesign', data=data, content_type='multipart/form-data')
        
        # Assert
        assert response.status_code == 500
        assert b'Failed to design room' in response.data
    
    def test_redesign_ai_service_raises_exception(self, client, mock_ai_service):
        """Test redesign when AI service raises exception."""
        # Arrange
        input_bytes = generate_test_image_bytes()
        mock_ai_service.generate_image.side_effect = Exception("API Error")
        
        data = {
            'file': (io.BytesIO(input_bytes), 'test.png'),
        }
        
        # Act
        response = client.post('/api/redesign', data=data, content_type='multipart/form-data')
        
        # Assert
        assert response.status_code == 500
        assert b'Failed to design room' in response.data
    
    def test_redesign_empty_mode_first_step_fails(self, client, mock_ai_service):
        """Test redesign in empty mode when first step fails."""
        # Arrange
        input_bytes = generate_test_image_bytes()
        mock_ai_service.generate_image.return_value = None
        
        data = {
            'file': (io.BytesIO(input_bytes), 'test.png'),
            'empty_then_generate': 'true'
        }
        
        # Act
        response = client.post('/api/redesign', data=data, content_type='multipart/form-data')
        
        # Assert
        assert response.status_code == 500
        assert b'Failed to empty room' in response.data
    
    def test_redesign_empty_mode_second_step_fails(self, client, mock_ai_service):
        """Test redesign in empty mode when second step fails."""
        # Arrange
        input_bytes = generate_test_image_bytes()
        empty_bytes = generate_test_image_bytes()
        mock_ai_service.generate_image.side_effect = [empty_bytes, None]
        
        data = {
            'file': (io.BytesIO(input_bytes), 'test.png'),
            'empty_then_generate': 'true'
        }
        
        # Act
        response = client.post('/api/redesign', data=data, content_type='multipart/form-data')
        
        # Assert
        assert response.status_code == 500
        assert b'Failed to design room' in response.data


class TestRefineRoute:
    """Tests for the /api/refine route."""
    
    def test_refine_success(self, client, mock_ai_service):
        """Test successful image refinement."""
        # Arrange
        input_data_uri = generate_test_data_uri()
        output_bytes = generate_test_image_bytes()
        mock_ai_service.generate_image.return_value = output_bytes
        
        data = {
            'image_data': input_data_uri,
            'prompt': 'Make it brighter'
        }
        
        # Act
        response = client.post('/api/refine', json=data)
        
        # Assert
        assert response.status_code == 200
        json_data = response.get_json()
        assert 'refined_image' in json_data
        assert json_data['refined_image'].startswith('data:image/')
        mock_ai_service.generate_image.assert_called_once()
    
    def test_refine_missing_image_data(self, client):
        """Test refine without image data."""
        # Arrange
        data = {
            'prompt': 'Make it brighter'
        }
        
        # Act
        response = client.post('/api/refine', json=data)
        
        # Assert
        assert response.status_code == 400
        assert b'Missing image data' in response.data
    
    def test_refine_missing_prompt(self, client):
        """Test refine without prompt."""
        # Arrange
        data = {
            'image_data': generate_test_data_uri()
        }
        
        # Act
        response = client.post('/api/refine', json=data)
        
        # Assert
        assert response.status_code == 400
        assert b'Missing prompt' in response.data
    
    def test_refine_empty_prompt(self, client):
        """Test refine with empty prompt."""
        # Arrange
        data = {
            'image_data': generate_test_data_uri(),
            'prompt': '   '  # Only whitespace
        }
        
        # Act
        response = client.post('/api/refine', json=data)
        
        # Assert
        assert response.status_code == 400
        assert b'Missing prompt' in response.data
    
    def test_refine_invalid_image_data(self, client):
        """Test refine with invalid image data."""
        # Arrange
        data = {
            'image_data': 'invalid-data-uri',
            'prompt': 'Make it brighter'
        }
        
        # Act
        response = client.post('/api/refine', json=data)
        
        # Assert
        assert response.status_code == 400
        assert b'Invalid image' in response.data
    
    def test_refine_ai_service_returns_none(self, client, mock_ai_service):
        """Test refine when AI service returns None."""
        # Arrange
        mock_ai_service.generate_image.return_value = None
        
        data = {
            'image_data': generate_test_data_uri(),
            'prompt': 'Make it brighter'
        }
        
        # Act
        response = client.post('/api/refine', json=data)
        
        # Assert
        assert response.status_code == 500
        assert b'Failed to refine' in response.data
    
    def test_refine_ai_service_raises_exception(self, client, mock_ai_service):
        """Test refine when AI service raises exception."""
        # Arrange
        mock_ai_service.generate_image.side_effect = Exception("API Error")
        
        data = {
            'image_data': generate_test_data_uri(),
            'prompt': 'Make it brighter'
        }
        
        # Act
        response = client.post('/api/refine', json=data)
        
        # Assert
        assert response.status_code == 500
        assert b'Failed to refine' in response.data
    
    def test_refine_invalid_json(self, client):
        """Test refine with invalid JSON."""
        # Act
        response = client.post('/api/refine', data='not-json', content_type='application/json')
        
        # Assert
        assert response.status_code == 400


class TestSearchFurnitureRoute:
    """Tests for the /api/search-furniture route."""
    
    def test_search_furniture_success(self, client, mock_search_service):
        """Test successful furniture search."""
        # Arrange
        input_bytes = generate_test_image_bytes()
        mock_search_service.search.return_value = [
            {'title': 'Sofa', 'price': '$500', 'score': 0.95}
        ]
        
        data = {
            'image': (io.BytesIO(input_bytes), 'test.png'),
            'box_x': '10',
            'box_y': '10',
            'box_width': '50',
            'box_height': '50'
        }
        
        # Act
        response = client.post('/api/search-furniture', data=data, content_type='multipart/form-data')
        
        # Assert
        assert response.status_code == 200
        json_data = response.get_json()
        assert 'results' in json_data
        assert len(json_data['results']) == 1
        assert json_data['results'][0]['title'] == 'Sofa'
    
    def test_search_furniture_no_image(self, client):
        """Test search without image."""
        # Arrange
        data = {
            'box_x': '10',
            'box_y': '10',
            'box_width': '50',
            'box_height': '50'
        }
        
        # Act
        response = client.post('/api/search-furniture', data=data, content_type='multipart/form-data')
        
        # Assert
        assert response.status_code == 400
        assert b'No image uploaded' in response.data
    
    def test_search_furniture_empty_filename(self, client):
        """Test search with empty filename."""
        # Arrange
        data = {
            'image': (io.BytesIO(b''), ''),
            'box_x': '10',
            'box_y': '10',
            'box_width': '50',
            'box_height': '50'
        }
        
        # Act
        response = client.post('/api/search-furniture', data=data, content_type='multipart/form-data')
        
        # Assert
        assert response.status_code == 400
        assert b'No file selected' in response.data
    
    def test_search_furniture_invalid_crop_values(self, client):
        """Test search with invalid crop box values."""
        # Arrange
        input_bytes = generate_test_image_bytes()
        data = {
            'image': (io.BytesIO(input_bytes), 'test.png'),
            'box_x': 'invalid',
            'box_y': '10',
            'box_width': '50',
            'box_height': '50'
        }
        
        # Act
        response = client.post('/api/search-furniture', data=data, content_type='multipart/form-data')
        
        # Assert
        assert response.status_code == 400
        assert b'Invalid crop box values' in response.data
    
    def test_search_furniture_missing_crop_width(self, client):
        """Test search with missing crop width."""
        # Arrange
        input_bytes = generate_test_image_bytes()
        data = {
            'image': (io.BytesIO(input_bytes), 'test.png'),
            'box_x': '10',
            'box_y': '10',
            'box_height': '50'
        }
        
        # Act
        response = client.post('/api/search-furniture', data=data, content_type='multipart/form-data')
        
        # Assert
        assert response.status_code == 400
        assert b'Invalid crop box values' in response.data
    
    def test_search_furniture_negative_dimensions(self, client):
        """Test search with negative crop dimensions."""
        # Arrange
        input_bytes = generate_test_image_bytes()
        data = {
            'image': (io.BytesIO(input_bytes), 'test.png'),
            'box_x': '10',
            'box_y': '10',
            'box_width': '-50',
            'box_height': '50'
        }
        
        # Act
        response = client.post('/api/search-furniture', data=data, content_type='multipart/form-data')
        
        # Assert
        assert response.status_code == 400
        assert b'Crop dimensions must be positive' in response.data
    
    def test_search_furniture_zero_dimensions(self, client):
        """Test search with zero crop dimensions."""
        # Arrange
        input_bytes = generate_test_image_bytes()
        data = {
            'image': (io.BytesIO(input_bytes), 'test.png'),
            'box_x': '10',
            'box_y': '10',
            'box_width': '0',
            'box_height': '50'
        }
        
        # Act
        response = client.post('/api/search-furniture', data=data, content_type='multipart/form-data')
        
        # Assert
        assert response.status_code == 400
        assert b'Crop dimensions must be positive' in response.data
    
    def test_search_furniture_empty_file(self, client):
        """Test search with empty file content."""
        # Arrange
        data = {
            'image': (io.BytesIO(b''), 'test.png'),
            'box_x': '10',
            'box_y': '10',
            'box_width': '50',
            'box_height': '50'
        }
        
        # Act
        response = client.post('/api/search-furniture', data=data, content_type='multipart/form-data')
        
        # Assert
        assert response.status_code == 400
        assert b'Empty file' in response.data
    
    def test_search_furniture_unsupported_file_type(self, client):
        """Test search with unsupported file type."""
        # Arrange - Create a GIF file
        img = Image.new('RGB', (100, 100), color='green')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='GIF')
        
        data = {
            'image': (io.BytesIO(img_byte_arr.getvalue()), 'test.gif'),
            'box_x': '10',
            'box_y': '10',
            'box_width': '50',
            'box_height': '50'
        }
        
        # Act
        response = client.post('/api/search-furniture', data=data, content_type='multipart/form-data')
        
        # Assert
        assert response.status_code == 400
        assert b'Unsupported file type' in response.data
    
    def test_search_furniture_service_not_initialized(self, client, mock_search_service):
        """Test search when service is not initialized."""
        # Arrange
        input_bytes = generate_test_image_bytes()
        mock_search_service.search.side_effect = RuntimeError("Service not initialized")
        
        data = {
            'image': (io.BytesIO(input_bytes), 'test.png'),
            'box_x': '10',
            'box_y': '10',
            'box_width': '50',
            'box_height': '50'
        }
        
        # Act
        response = client.post('/api/search-furniture', data=data, content_type='multipart/form-data')
        
        # Assert
        assert response.status_code == 503
        assert b'Search unavailable' in response.data
    
    def test_search_furniture_unexpected_exception(self, client, mock_search_service):
        """Test search with unexpected exception."""
        # Arrange
        input_bytes = generate_test_image_bytes()
        mock_search_service.search.side_effect = Exception("Unexpected error")
        
        data = {
            'image': (io.BytesIO(input_bytes), 'test.png'),
            'box_x': '10',
            'box_y': '10',
            'box_width': '50',
            'box_height': '50'
        }
        
        # Act
        response = client.post('/api/search-furniture', data=data, content_type='multipart/form-data')
        
        # Assert
        assert response.status_code == 500
        assert b'Failed to search furniture' in response.data
    
    def test_search_furniture_with_default_coordinates(self, client, mock_search_service):
        """Test search with default x,y coordinates."""
        # Arrange
        input_bytes = generate_test_image_bytes()
        mock_search_service.search.return_value = []
        
        data = {
            'image': (io.BytesIO(input_bytes), 'test.png'),
            # box_x and box_y default to 0
            'box_width': '50',
            'box_height': '50'
        }
        
        # Act
        response = client.post('/api/search-furniture', data=data, content_type='multipart/form-data')
        
        # Assert
        assert response.status_code == 200


class TestGetServices:
    """Tests for the _get_services helper function."""
    
    def test_get_services_missing_services(self, app):
        """Test _get_services when services are not initialized."""
        # Arrange
        app.extensions.clear()
        
        with app.test_request_context():
            from backend.api.routes import _get_services
            
            # Act & Assert
            with pytest.raises(RuntimeError, match="Services not initialized"):
                _get_services()
