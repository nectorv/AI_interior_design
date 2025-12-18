# Legacy app.py - kept for backward compatibility
# New entry point: run.py or python -m backend.app
# This file redirects to the new modular structure

from backend.app import create_app

app = create_app()

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)