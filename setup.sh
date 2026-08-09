#!/bin/bash

# GPUCT Container Management System Setup Script

echo "Setting up GPUCT Container Management System..."

# Check if Python 3.8+ is available
python3_version=$(python3 --version 2>&1 | grep -Po '(?<=Python )(.+)')
if [[ -z "$python3_version" ]]; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

echo "Found Python $python3_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "Creating directories..."
mkdir -p logs ssh_keys config app templates scripts

# Set proper permissions
chmod 700 ssh_keys
chmod 755 logs

# Check for Incus installation
if ! command -v incus &> /dev/null; then
    echo ""
    echo "WARNING: Incus is not installed!"
    echo "To install Incus on Ubuntu, run:"
    echo "  sudo snap install incus --classic"
    echo "  sudo incus admin init"
    echo ""
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file template..."
    cat > .env << 'ENVEOF'
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=mac4@spit.ac.in
SMTP_PASSWORD=irqr abzg tvrr dkzh
FROM_EMAIL=mac4@spit.ac.in
ENVEOF
    echo "Created .env file with email configuration"
else
    echo ".env file already exists"
fi

echo ""
echo "Setup completed successfully!"
echo ""
echo "To start the server, run:"
echo "  ./start_server.sh"
echo ""
echo "API will be available at:"
echo "  http://localhost:8000"
echo "  Documentation: http://localhost:8000/docs"
