"""Application entry point."""
import logging
import sys
from backend.app import create_app

# Configure logging to ensure errors are visible
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

if __name__ == "__main__":
    app = create_app()
    # Bind to 0.0.0.0 so Docker/Codespaces can reach the server
    app.run(host="0.0.0.0", port=5000, debug=True)
