# AI Interior Designer

A personal project that uses AI to modify interior design spaces. Upload a photo of your room and redesign it in your chosen style.

## 🎨 Live Demo

**Try the live demo here:** https://ap2bcuij5s.eu-central-1.awsapprunner.com/

Simply upload a room photo, select a design style, and watch the magic happen!

The live demo features a Qdrant vector database with a custom dataset of over 65,000 furniture items, powered by a Lambda function running a fine-tuned CLIP ViT-32 model for intelligent furniture search.

## 🛠 Tech Stack

### Backend
- **Flask** - Python web framework
- **Google Gemini API** - AI image generation
- **Pillow** - Image processing
- **Qdrant** - Vector database for furniture search
- **Docker** - Containerization

### Frontend
- **HTML/CSS/JavaScript** - Vanilla JavaScript (no framework)

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Docker
- Google Gemini API Key

### Environment Variables

Create a `.env` file with the following variables:

```bash
GOOGLE_API_KEY=your-google-gemini-api-key
QDRANT_URL=http://localhost:6333  # Optional
QDRANT_API_KEY=your-qdrant-api-key  # Optional
QDRANT_COLLECTION_NAME=furniture_items
FLASK_ENV=development
```

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd AI_interior_design

# Build and start the application
docker-compose up --build

# Application will be available at http://localhost:5000
```

## 🏗 Project Structure

```
AI_interior_design/
├── backend/
│   ├── api/              # Flask routes and endpoints
│   ├── core/             # Configuration and prompts
│   ├── services/         # AI and image services
│   └── utils/            # Image processing utilities
├── templates/            # HTML templates
├── static/
│   ├── css/              # Styling
│   └── js/               # Frontend JavaScript
├── Dockerfile            # Container configuration
├── docker-compose.yml    # Multi-container setup
├── requirements.txt      # Python dependencies
└── run.py                # Application entry point
```

### Deploy with AWS App Runner

The application is ready to be deployed with AWS App Runner:

1. Connect your ECR repository to App Runner
2. Set environment variables in the App Runner configuration
3. Deploy with automatic scaling and health checks

## 🎯 Future Enhancements

- [ ] User authentication and design history
- [ ] Design sharing and collaboration
- [ ] Mobile app (iOS/Android)
- [ ] Multi-room project support
