#!/bin/bash

echo "🚀 AI Lead Scoring System - Quick Start"
echo "========================================"
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check for .env file
if [ ! -f .env ]; then
    echo ""
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo "✏️  Please edit .env and add your API keys:"
    echo "   - OPENAI_API_KEY"
    echo "   - GHL_API_KEY"
    echo "   - SLACK_WEBHOOK_URL"
    echo "   - Lead owner IDs"
    echo ""
    read -p "Press Enter after you've updated .env..."
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the server:"
echo "  source venv/bin/activate"
echo "  python main.py"
echo ""
echo "Or using Docker:"
echo "  docker-compose up"
echo ""
echo "API will be available at http://localhost:8000"
echo "Docs at http://localhost:8000/docs"
