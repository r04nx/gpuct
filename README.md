# SPIT-CTF Container Management System

A comprehensive FastAPI-based system for creating, managing, and monitoring Ubuntu containers with SSH access using Incus.

## Features

- **Container Creation**: Create Ubuntu 22.04 containers with custom RAM and storage specifications
- **SSH Access**: Automatic SSH server setup with key-based authentication
- **Email Notifications**: Automated email delivery with connection details and private keys
- **Container Lifecycle**: Automatic container expiration and cleanup based on specified days
- **REST API**: Full REST API with interactive documentation
- **Security**: Input validation, command sanitization, and secure execution
- **Scheduling**: Background tasks for container management and notifications

## Prerequisites

- Ubuntu 20.04 or later
- Python 3.8 or later
- Incus (LXD successor)
- Email account with app password (Gmail configured by default)

## Quick Start

1. **Clone and Setup**
   ```bash
   git clone <repository>
   cd SPIT-CTF
   ./setup.sh
   ```

2. **Install Incus** (if not already installed)
   ```bash
   sudo snap install incus --classic
   sudo incus admin init
   ```

3. **Start the Server**
   ```bash
   ./start_server.sh
   ```

4. **Access the API**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs

## API Endpoints

### Container Management

#### Create Container
```http
POST /containers/
```

Request body:
```json
{
  "username": "student123",
  "password": "SecurePass123",
  "ram": "2GB",
  "storage": "20GB",
  "student_email": "student@example.com",
  "days_to_live": 7
}
```

Response:
```json
{
  "success": true,
  "message": "Container student123-1697123456 created successfully. Email notification sent to student@example.com",
  "data": {
    "container_name": "student123-1697123456",
    "ip_address": "10.10.1.100",
    "username": "student123",
    "expires_at": "2023-10-20T12:00:00"
  }
}
```

#### List Containers
```http
GET /containers/
```

#### Get Container Details
```http
GET /containers/{container_name}
```

#### Freeze Container
```http
POST /containers/{container_name}/freeze
```

#### Delete Container
```http
DELETE /containers/{container_name}
```

#### Cleanup Expired Containers
```http
POST /containers/cleanup
```

### System

#### Health Check
```http
GET /health
```

## Email Configuration

The system sends emails with container details and SSH keys. Configure email settings in `.env`:

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=your_email@gmail.com
```

## Container Specifications

### Resource Limits
- **RAM**: 512MB to 8GB
- **Storage**: 1GB to 100GB
- **Operating System**: Ubuntu 22.04 (latest)

### Default Configuration
- **RAM**: 1GB
- **Storage**: 10GB
- **SSH**: Enabled with key-based authentication
- **User**: sudo access enabled

## SSH Connection

After container creation, you'll receive an email with:
1. Container IP address
2. Username
3. Private SSH key (attached file)

### Connection Steps

1. **Save the SSH key**
   ```bash
   chmod 600 username-containername.pem
   ```

2. **Connect via SSH**
   ```bash
   ssh -i username-containername.pem username@container-ip
   ```

3. **Alternative (password authentication)**
   ```bash
   ssh username@container-ip
   # Use the password provided during creation
   ```

## Container Lifecycle

1. **Creation**: Container is created with specified resources
2. **Active**: Container runs for the specified number of days
3. **Warning**: Email notifications sent 3 and 1 days before expiration
4. **Expiration**: Container is automatically frozen
5. **Cleanup**: Frozen containers can be manually deleted

## Security Features

- Input validation and sanitization
- Command injection prevention
- Resource limit enforcement
- Secure SSH key generation
- Safe file path handling
- Audit logging

## Directory Structure

```
GPUCT/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── container_manager.py # Container management logic
│   ├── email_service.py     # Email functionality
│   ├── models.py           # Pydantic models
│   ├── scheduler.py        # Background tasks
│   └── security.py         # Security utilities
├── config/
│   ├── __init__.py
│   └── settings.py         # Configuration settings
├── logs/                   # Application logs
├── ssh_keys/              # Generated SSH keys
├── templates/             # Email templates
├── scripts/               # Utility scripts
├── .env                   # Environment variables
├── requirements.txt       # Python dependencies
├── setup.sh              # Setup script
├── start_server.sh       # Server startup script
└── README.md             # This file
```

## Development

### Running in Development Mode

```bash
# Activate virtual environment
source venv/bin/activate

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start with auto-reload
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Adding New Features

1. Update models in `app/models.py`
2. Add business logic to appropriate service classes
3. Add API endpoints in `app/main.py`
4. Update documentation

### Testing Container Creation

```python
import requests

# Create container
response = requests.post("http://localhost:8000/containers/", json={
    "username": "testuser",
    "password": "TestPass123",
    "ram": "1GB",
    "storage": "10GB",
    "student_email": "test@example.com",
    "days_to_live": 7
})

print(response.json())
```

## Troubleshooting

### Common Issues

1. **Incus not found**
   ```bash
   sudo snap install incus --classic
   sudo incus admin init
   ```

2. **Permission denied for SSH keys**
   ```bash
   chmod 600 ssh_keys/*.pem
   ```

3. **Email sending fails**
   - Check email credentials in `.env`
   - Ensure app password is used for Gmail
   - Verify network connectivity

4. **Container creation fails**
   - Check Incus status: `incus info`
   - Verify available resources
   - Check logs: `tail -f logs/gpuct.log`

### Logs

Application logs are stored in `logs/gpuct.log`. Monitor in real-time:

```bash
tail -f logs/gpuct.log
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SMTP_SERVER` | Email server | smtp.gmail.com |
| `SMTP_PORT` | Email port | 587 |
| `SMTP_USERNAME` | Email username | - |
| `SMTP_PASSWORD` | Email password | - |
| `FROM_EMAIL` | Sender email | - |
| `LOG_LEVEL` | Logging level | INFO |

### Default Settings

Edit `config/settings.py` to modify default values:
- Container resources
- Network configuration
- SSH key settings
- Logging configuration

## Production Deployment

### Systemd Service

Create `/etc/systemd/system/gpuct.service`:

```ini
[Unit]
Description=GPUCT Container Management System
After=network.target

[Service]
Type=simple
User=gpuct
WorkingDirectory=/opt/gpuct
Environment=PATH=/opt/gpuct/venv/bin
Environment=PYTHONPATH=/opt/gpuct
ExecStart=/opt/gpuct/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable gpuct
sudo systemctl start gpuct
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Email: sushant.goswami@spit.ac.in
- Check logs: `logs/gpuct.log`
- API Documentation: http://localhost:8000/docs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with proper tests
4. Submit a pull request

---

**SPIT-CTF Container Management System** - Automated container provisioning with SSH access and email notifications.
