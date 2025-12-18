"""Application entry point."""
from backend.app import create_app


if __name__ == "__main__":
    app = create_app()
    # Bind to 0.0.0.0 so Docker/Codespaces can reach the server
    app.run(host="0.0.0.0", port=5000, debug=True)
