# AI Interior Designer

A professional AI-powered interior design application that allows users to redesign rooms using AI image generation and furniture search capabilities.

## Project Structure

```
ai-interior-designer/
├── backend/                    # Python backend application
│   ├── api/                    # API layer (routes & request handling)
│   │   ├── __init__.py
│   │   └── routes.py           # All Flask route handlers
│   ├── services/               # Business logic layer
│   │   ├── __init__.py
│   │   ├── ai_service.py       # Gemini AI service
│   │   ├── search_service.py   # Furniture search service (CLIP)
│   │   └── image_service.py    # Image processing utilities
│   ├── core/                   # Core domain logic
│   │   ├── __init__.py
│   │   ├── config.py           # Configuration management
│   │   └── prompts.py           # Prompt templates
│   ├── utils/                  # Utility functions
│   │   ├── __init__.py
│   │   └── image_utils.py      # Image encoding/decoding
│   └── app.py                  # Flask application factory
│
├── static/                     # Frontend static files
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   ├── main.js            # Application entry point
│   │   └── modules/
│   │       ├── api.js         # API communication
│   │       ├── ui.js          # UI manipulation
│   │       └── editor.js      # Image editing logic
│   └── assets/                # Images, fonts, etc.
│
├── templates/                  # HTML templates
│   └── index.html
│
├── scripts/                    # Utility scripts
│   └── pack_context.py
│
├── tests/                      # Test suite
│   └── __init__.py
│
├── google_dataset/             # Dataset files (CSV, embeddings)
├── outputs/                    # Generated outputs
├── temp/                       # Temporary files
│
├── run.py                      # Application entry point
├── app.py                      # Legacy entry point (backward compatibility)
├── requirements.txt
└── README.md
```

## Architecture

### Backend Structure

The backend follows a **layered architecture**:

1. **API Layer** (`backend/api/`): Handles HTTP requests and responses
2. **Service Layer** (`backend/services/`): Contains business logic
3. **Core Layer** (`backend/core/`): Domain logic (prompts, configuration)
4. **Utils Layer** (`backend/utils/`): Reusable utility functions

### Design Principles

- **Separation of Concerns**: Clear boundaries between layers
- **Single Responsibility**: Each module has one clear purpose
- **Modularity**: Easy to add new features or modify existing ones
- **Testability**: Services can be tested independently

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
Create a `.env` file with:
```
GOOGLE_API_KEY=your_api_key_here
```

3. Run the application:
```bash
python run.py
```

Or use the legacy entry point:
```bash
python app.py
```

## API Endpoints

- `GET /` - Main application page
- `POST /api/redesign` - Redesign a room image
- `POST /api/refine` - Refine an existing design
- `POST /api/search-furniture` - Search for furniture based on image crop

## Development

### Adding New Features

1. **New API Endpoint**: Add to `backend/api/routes.py`
2. **New Service**: Create in `backend/services/`
3. **New Utility**: Add to `backend/utils/`
4. **Configuration**: Update `backend/core/config.py`

### Testing

Tests should be placed in the `tests/` directory following the same structure as the backend.

## Technologies

- **Backend**: Python, Flask
- **AI**: Google Gemini API
- **Search**: CLIP (Hugging Face Transformers)
- **Frontend**: Vanilla JavaScript, HTML, CSS

