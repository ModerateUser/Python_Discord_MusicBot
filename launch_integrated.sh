#!/bin/bash
# Discord Music Bot - Integrated Launcher (Linux/Mac)
# Launches bot with web dashboard in same process

echo "========================================"
echo "Discord Music Bot - Integrated Mode"
echo "Bot + Web Dashboard"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Python version: $PYTHON_VERSION"

# Check if config.json exists
if [ ! -f "config.json" ]; then
    echo "ERROR: config.json not found!"
    echo ""
    echo "Please create config.json from config.example.json:"
    echo "  1. Copy config.example.json to config.json"
    echo "  2. Edit config.json and add your Discord bot token"
    echo "  3. Configure other settings as needed"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        read -p "Press Enter to exit..."
        exit 1
    fi
    echo "Virtual environment created successfully!"
    echo ""
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment"
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if dependencies are installed
echo "Checking dependencies..."
python3 -c "import discord, fastapi" &> /dev/null
if [ $? -ne 0 ]; then
    echo "Dependencies not installed. Installing from requirements.txt..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies"
        read -p "Press Enter to exit..."
        exit 1
    fi
    echo "Dependencies installed successfully!"
    echo ""
fi

# Launch the integrated bot
echo "========================================"
echo "Starting Discord Music Bot with Dashboard"
echo "========================================"
echo ""
echo "Dashboard will be available at:"
echo "  http://localhost:8000"
echo ""
echo "API Documentation:"
echo "  http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both bot and dashboard"
echo "========================================"
echo ""

python3 bot_with_dashboard.py

# Check exit status
if [ $? -ne 0 ]; then
    echo ""
    echo "========================================"
    echo "System stopped with an error"
    echo "Check the logs above for details"
    echo "========================================"
    read -p "Press Enter to exit..."
    exit 1
fi

echo ""
echo "System stopped normally"
read -p "Press Enter to exit..."
