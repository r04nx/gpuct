from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List
import logging
import sys
import os
from datetime import datetime
from contextlib import asynccontextmanager
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import (
    ContainerCreateRequest, ContainerResponse, ContainerListResponse, 
    ApiResponse, HealthCheckResponse, WebContainerCreateRequest
)
from app.container_manager import ContainerManager
from app.email_service import EmailService
from config.settings import settings
from app.scheduler import start_background_scheduler, stop_background_scheduler

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting SPIT-CTF Container Management System...")
    try:
        start_background_scheduler()
        logger.info("Background scheduler started")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {str(e)}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down SPIT-CTF Container Management System...")
    try:
        stop_background_scheduler()
        logger.info("Background scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {str(e)}")

# Create FastAPI app
app = FastAPI(
    title="🚀 SPIT-CTF Container Management System",
    description="""
    ## 📋 Overview
    A comprehensive container management system for creating, managing, and monitoring Ubuntu containers with SSH access.
    
    ## ✨ Features
    * 🐳 **Container Creation**: Ubuntu 22.04 containers with custom specifications
    * 🔐 **SSH Access**: Automatic SSH key generation and setup  
    * 📧 **Email Notifications**: Automated email delivery with connection details
    * ⏰ **Lifecycle Management**: Automatic container expiration and cleanup
    * 📚 **REST API**: Full REST API with interactive documentation
    * 🛡️ **Security**: Input validation and secure execution
    
    ## 🔧 Quick Start
    1. **Create Container**: Use the `/containers/` POST endpoint below
    2. **Check Email**: Receive SSH keys and connection details
    3. **Connect**: SSH to your container using the provided key
    4. **Manage**: Use other endpoints to monitor and manage containers
    
    ## 📞 Support
    For assistance, contact: **sushant.goswami@spit.ac.in**
    """,
    version="1.0.0",
    contact={
        "name": "GPUCT Admin", 
        "email": "sushant.goswami@spit.ac.in"
    },
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "containers",
            "description": "Container management operations - create, list, manage containers"
        },
        {
            "name": "system", 
            "description": "System health and information endpoints"
        }
    ]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
container_manager = ContainerManager()
email_service = EmailService()

# Custom exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.now().isoformat(),
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.now().isoformat(),
            "status_code": 500
        }
    )

async def send_container_email(container_info: dict):
    """Background task to send container notification email"""
    try:
        success = await email_service.send_container_notification(container_info)
        if success:
            logger.info(f"Email sent successfully for container {container_info['name']}")
        else:
            logger.error(f"Failed to send email for container {container_info['name']}")
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")

@app.get("/", response_model=dict, tags=["system"])
async def root():
    """
    🏠 **Welcome to SPIT-CTF Container Management System**
    
    Get basic API information and available endpoints.
    """
    return {
        "message": "🚀 Welcome to SPIT-CTF Container Management System",
        "version": "1.0.0",
        "status": "running", 
        "docs_url": "/docs",
        "health_check": "/health",
        "features": [
            "🐳 Ubuntu Container Creation",
            "🔐 SSH Key Management",
            "📧 Email Notifications", 
            "⏰ Lifecycle Management"
        ],
        "endpoints": {
            "create_container": "POST /containers/",
            "list_containers": "GET /containers/",
            "get_container": "GET /containers/{container_name}",
            "freeze_container": "POST /containers/{container_name}/freeze",
            "delete_container": "DELETE /containers/{container_name}"
        }
    }

@app.get("/health", response_model=HealthCheckResponse, tags=["system"])
async def health_check():
    """
    🏥 **System Health Check**
    
    Check the health status of all system components including Incus, email service, and API.
    """
    try:
        # Check if incus is available
        import subprocess
        result = subprocess.run(["incus", "--version"], capture_output=True, text=True)
        incus_available = result.returncode == 0
        incus_version = result.stdout.strip() if incus_available else "not available"
        
        services = {
            "incus": f"available (v{incus_version})" if incus_available else "unavailable",
            "email": "configured" if settings.SMTP_USERNAME else "not configured",
            "api": "running",
            "scheduler": "active"
        }
        
        overall_status = "healthy" if all("unavailable" not in s for s in services.values()) else "degraded"
        
        return HealthCheckResponse(
            status=overall_status,
            timestamp=datetime.now(),
            services=services
        )
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return HealthCheckResponse(
            status="unhealthy", 
            timestamp=datetime.now(),
            services={"error": str(e)}
        )

@app.post("/containers/",
         response_model=ApiResponse,
         status_code=status.HTTP_201_CREATED,
         tags=["containers"],
         summary="🐳 Create New Container",
         description="Create a new Ubuntu 22.04 container with custom specifications, SSH access, and email notifications")
async def create_container(request: ContainerCreateRequest, background_tasks: BackgroundTasks):
    """
    ## 🐳 Create a New Ubuntu Container
    
    **This endpoint will:**
    1. ✅ Create an Ubuntu 22.04 container with your specified resources
    2. 👤 Set up a user account with the provided username and password  
    3. 🔐 Generate and configure SSH keys for secure access
    4. 🌐 Configure DHCP to automatically assign an IP address
    5. 📧 Send you an email with connection details and the private SSH key
    6. ⏰ Set up automatic expiration based on your specified days
    
    **After creation, you'll receive:**
    - 📧 Email with SSH connection instructions
    - 🔑 Private SSH key file (attached to email)
    - 🌐 Container IP address and connection details
    - 📋 Complete setup and usage guide
    
    **Example SSH Connection:**
    ```bash
    # After receiving the email:
    chmod 600 your-username-containername.pem
    ssh -i your-username-containername.pem username@container-ip
    ```
    """
    try:
        logger.info(f"🚀 Creating container for user: {request.username}")
        
        # Create the container
        container_info = await container_manager.create_container(
            username=request.username,
            password=request.password,
            ram=request.ram,
            storage=request.storage,
            student_email=request.student_email,
            days_to_live=request.days_to_live
        )
        
        # Send email notification in background
        background_tasks.add_task(send_container_email, container_info)
        
        logger.info(f"✅ Container {container_info['name']} created successfully")
        
        return ApiResponse(
            success=True,
            message=f"🎉 Container '{container_info['name']}' created successfully! Email notification sent to {request.student_email}",
            data={
                "container_name": container_info['name'],
                "ip_address": container_info['ip_address'],
                "username": request.username,
                "expires_at": container_info['expires_at'],
                "ssh_command": f"ssh -i {request.username}-{container_info['name']}.pem {request.username}@{container_info['ip_address']}"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to create container: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Container creation failed: {str(e)}"
        )

@app.get("/containers/",
        response_model=ContainerListResponse,
        tags=["containers"],
        summary="📋 List All Containers", 
        description="Get a list of all managed containers with their current status and details")
async def list_containers():
    """
    ## 📋 List All Managed Containers
    
    Returns a comprehensive list of all containers created through this system,
    including their current status, expiration dates, and connection details.
    
    **Container Status Values:**
    - 🟢 `running` - Container is active and accessible
    - 🟡 `frozen` - Container is paused/frozen (expired)
    - 🔴 `stopped` - Container is stopped
    """
    try:
        containers = await container_manager.list_containers()
        
        return ContainerListResponse(
            containers=[ContainerResponse(**container) for container in containers],
            total=len(containers)
        )
        
    except Exception as e:
        logger.error(f"Failed to list containers: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list containers: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
