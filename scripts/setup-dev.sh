#!/bin/bash

echo "🚀 Setting up development environment..."

echo "📦 Installing development dependencies..."
pip install -e ".[dev]"

echo "🔧 Installing pre-commit hooks..."
pre-commit install

echo "✅ Running pre-commit on all files..."
pre-commit run --all-files

echo "🎉 Development environment setup complete!"
echo ""
echo "📝 Usage:"
echo "  - Ruff will now run automatically on every commit"
echo "  - To run manually: ruff check . && ruff format ."
echo "  - To run pre-commit manually: pre-commit run --all-files"
echo "  - To skip pre-commit on a commit: git commit --no-verify"
