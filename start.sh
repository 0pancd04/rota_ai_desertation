#!/bin/bash
echo "Starting AI Rota System..."

# Check if .venv exists, if not create it
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
fi

# Activate virtual environment and install dependencies
echo "Installing dependencies..."
uv pip install -e .

# Start the FastAPI server
echo "Starting FastAPI server..."
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload 