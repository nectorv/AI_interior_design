"""Flask application factory."""
import os
from flask import Flask
from backend.core.config import Config
from backend.api.routes import api_bp
from backend.services.ai_service import GeminiService
from backend.services.search_service import FurnitureSearcher


def create_app():
    """Create and configure the Flask application.
    
    Returns:
        Configured Flask application instance
    """
    # Get the root directory (parent of backend/)
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    app = Flask(
        __name__,
        template_folder=os.path.join(root_dir, 'templates'),
        static_folder=os.path.join(root_dir, 'static')
    )
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

    # Initialize shared services once and store on the app
    app.extensions['ai_service'] = GeminiService()
    app.extensions['search_service'] = FurnitureSearcher()

    # Register blueprints
    app.register_blueprint(api_bp)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

