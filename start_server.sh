#!/bin/bash

# SPIT-CTF Container Management System Startup Script

echo "Starting SPIT-CTF Container Management System..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if logs directory exists
if [ ! -d "logs" ]; then
    mkdir -p logs
fi

# Check if ssh_keys directory exists
if [ ! -d "ssh_keys" ]; then
    mkdir -p ssh_keys
    chmod 700 ssh_keys
fi

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Using default settings."
fi

# Check if Incus is available
if ! command -v incus &> /dev/null; then
    echo "Warning: Incus is not installed or not in PATH"
    echo "Please install Incus for container management functionality"
fi

# Start the FastAPI server
echo "Starting FastAPI server on http://0.0.0.0:8000"
echo "API Documentation available at http://0.0.0.0:8000/docs"
echo "Press Ctrl+C to stop the server"

cd app
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
