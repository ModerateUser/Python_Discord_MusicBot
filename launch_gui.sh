#!/bin/bash

# Discord Music Bot - Web Dashboard Launcher (Linux/Mac)
# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================"
echo "  Discord Music Bot - Web Dashboard"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo -e "${BLUE}[INFO]${NC} Python version: $(python3 --version)"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}[SETUP]${NC} Virtual environment not found. Creating..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR]${NC} Failed to create virtual environment"
        exit 1
    fi
    echo -e "${GREEN}[SUCCESS]${NC} Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo -e "${BLUE}[INFO]${NC} Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR]${NC} Failed to activate virtual environment"
    exit 1
fi

# Check if config.json exists
if [ ! -f "config.json" ]; then
    echo -e "${YELLOW}[WARNING]${NC} config.json not found!"
    echo "The dashboard will still work, but bot integration requires config.json"
    echo ""
fi

# Check if FastAPI dependencies are installed
echo -e "${BLUE}[INFO]${NC} Checking dashboard dependencies..."
python3 -c "import fastapi, uvicorn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}[SETUP]${NC} Installing dashboard dependencies..."
    python3 -m pip install --upgrade pip
    pip install fastapi "uvicorn[standard]" jinja2 python-multipart websockets
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR]${NC} Failed to install dependencies"
        exit 1
    fi
    echo -e "${GREEN}[SUCCESS]${NC} Dependencies installed"
    echo ""
fi

# Check if templates directory exists
if [ ! -d "web_dashboard/templates" ]; then
    echo -e "${RED}[ERROR]${NC} Templates directory not found!"
    echo "Please ensure web_dashboard/templates/ exists with dashboard.html"
    exit 1
fi

# Create static directory if it doesn't exist
if [ ! -d "web_dashboard/static" ]; then
    echo -e "${BLUE}[INFO]${NC} Creating static directory..."
    mkdir -p web_dashboard/static/css
    mkdir -p web_dashboard/static/js
fi

# Run the dashboard
echo -e "${BLUE}[INFO]${NC} Starting Web Dashboard..."
echo "========================================"
echo ""
echo "Dashboard will be available at:"
echo "  http://localhost:8000"
echo ""
echo "API Documentation:"
echo "  http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the dashboard"
echo "========================================"
echo ""

cd web_dashboard
python3 app.py

# Handle errors
if [ $? -ne 0 ]; then
    echo ""
    echo "========================================"
    echo -e "${RED}[ERROR]${NC} Dashboard stopped with an error"
    echo "========================================"
fi

echo ""
read -p "Press Enter to exit..."
