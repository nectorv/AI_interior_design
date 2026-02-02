#!/bin/bash

echo "Installing pre-commit hooks..."
pip install pre-commit
pre-commit install

echo "Pre-commit hooks installed successfully!"
echo "Tests will now run automatically before each commit."
echo "To bypass hooks (not recommended): git commit --no-verify"
