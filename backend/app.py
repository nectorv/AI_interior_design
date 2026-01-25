"""Flask application factory."""
import logging
import os
from flask import Flask
from backend.core.config import Config
from backend.api.routes import api_bp
from backend.services.ai_service import GeminiService
from backend.services.lambda_search_service import LambdaFurnitureSearcher

logger = logging.getLogger(__name__)


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
    logger.info("Initializing AI service...")
    app.extensions['ai_service'] = GeminiService()
    
    logger.info("Initializing search service (Lambda adapter)...")
    search_service = LambdaFurnitureSearcher()
    app.extensions['search_service'] = search_service
    
    # Validate search service initialization
    if search_service.df_data is None:
        logger.error("WARNING: Search service failed to initialize. Furniture search will not work.")
        logger.error("Please ensure the following files exist and are readable:")
        logger.error("  - %s", Config.CSV_FILE)
        logger.error("  - %s", Config.EMBEDDINGS_FILE)
    else:
        logger.info("All services initialized successfully.")

    # Register blueprints
    app.register_blueprint(api_bp)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

