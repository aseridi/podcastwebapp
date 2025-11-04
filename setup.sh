#!/bin/bash

# Podcast Script Generator Setup Script

echo " Podcast Script Generator Setup"
echo "===================================="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Python $PYTHON_VERSION detected"
echo ""

# Create virtual environment
echo " Creating virtual environment..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "Failed to create virtual environment"
    exit 1
fi

echo "✓ Virtual environment created"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆Upgrading pip..."
pip install --upgrade pip -q

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -q

if [ $? -ne 0 ]; then
    echo "Failed to install dependencies"
    exit 1
fi

echo "✓ Dependencies installed"
echo ""

# Setup .env file
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "IMPORTANT: Please edit .env and add your API keys:"
    echo "   - GOOGLE_API_KEY"
    echo "   - DEEPSEEK_KEY"
    echo ""
else
    echo "✓ .env file already exists"
    echo ""
fi

# Create output directories
echo "Creating output directories..."
mkdir -p outputs/json outputs/scripts logs
echo "✓ Output directories created"
echo ""

# Summary
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env file and add your API keys"
echo "  2. Activate virtual environment: source venv/bin/activate"
echo "  3. Run the application: python app.py"
echo "  4. Open browser: http://localhost:5000"
echo ""
echo "Or use CLI: ./generate_cli.py --help"
echo ""
echo "Happy podcasting! "
