#!/bin/bash

# Install GPUCT as a systemd service

SERVICE_NAME="gpuct"
WORKING_DIR=$(pwd)
USER=$(whoami)

echo "Installing GPUCT Container Management System as systemd service..."

# Create systemd service file
sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<EOL
[Unit]
Description=GPUCT Container Management System
After=network.target
Wants=network.target

[Service]
Type=simple
User=${USER}
Group=${USER}
WorkingDirectory=${WORKING_DIR}
Environment=PATH=${WORKING_DIR}/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=PYTHONPATH=${WORKING_DIR}
ExecStart=${WORKING_DIR}/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}

echo "Service installed successfully!"
echo ""
echo "To start the service:"
echo "  sudo systemctl start ${SERVICE_NAME}"
echo ""
echo "To check status:"
echo "  sudo systemctl status ${SERVICE_NAME}"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u ${SERVICE_NAME} -f"
