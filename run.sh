#!/bin/bash

# Agentic Calendar Spread Trading System - Run Script

# Check if virtual environment exists
# Note: venv/ directory is excluded from Git via .gitignore
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Set environment variables
export FLASK_APP=app.py
export FLASK_ENV=development
export FLASK_DEBUG=True

# Run the application
echo "Starting Flask application..."
echo "Application will be available at: http://localhost:5001"
python app.py
