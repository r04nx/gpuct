from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
import re

class ContainerCreateRequest(BaseModel):
    username: str = Field(
        ..., 
        min_length=3, 
        max_length=32, 
        title="Linux Username",
        description="Username for the container (3-32 characters, lowercase letters, numbers, hyphens, underscores only)",
        example="student123"
    )
    password: str = Field(
        ..., 
        min_length=8, 
        title="Password",
        description="Password for the user account (minimum 8 characters, must contain letters and numbers)",
        example="SecurePass123"
    )
    ram: str = Field(
        default="1GB", 
        title="RAM Allocation",
        description="Memory allocation for the container (e.g., '1GB', '2GB', '512MB')",
        example="2GB"
    )
    storage: str = Field(
        default="10GB", 
        title="Storage Allocation",
        description="Disk space allocation for the container (e.g., '10GB', '20GB', '5GB')",
        example="15GB"
    )
    student_email: EmailStr = Field(
        ..., 
        title="Student Email",
        description="Email address where container details and SSH key will be sent",
        example="student@spit.ac.in"
    )
    days_to_live: int = Field(
        default=7, 
        ge=1, 
        le=365, 
        title="Days to Live",
        description="Number of days the container will remain active before automatic freezing (1-365 days)",
        example=14
    )

    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-z][a-z0-9_-]*$', v):
            raise ValueError('Username must start with a letter and contain only lowercase letters, numbers, hyphens, and underscores')
        reserved_names = ['root', 'admin', 'administrator', 'guest', 'daemon', 'sys', 'sync']
        if v.lower() in reserved_names:
            raise ValueError('Username not allowed (reserved name)')
        return v

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        return v

    @validator('ram')
    def validate_ram(cls, v):
        if not re.match(r'^\d+(\.\d+)?(MB|GB)$', v):
            raise ValueError('RAM must be in format like "1GB" or "512MB"')
        return v

    @validator('storage')
    def validate_storage(cls, v):
        if not re.match(r'^\d+(\.\d+)?(MB|GB|TB)$', v):
            raise ValueError('Storage must be in format like "10GB" or "1TB"')
        return v

    class Config:
        schema_extra = {
            "example": {
                "username": "student123",
                "password": "SecurePass123",
                "ram": "2GB",
                "storage": "15GB",
                "student_email": "student@spit.ac.in",
                "days_to_live": 14
            }
        }

class ContainerResponse(BaseModel):
    name: str = Field(..., title="Container Name", description="Unique container identifier")
    username: str = Field(..., title="Username", description="Linux username in the container")
    ip_address: str = Field(..., title="IP Address", description="Container's IP address")
    student_email: str = Field(..., title="Student Email", description="Email address for notifications")
    created_at: str = Field(..., title="Created At", description="Container creation timestamp")
    expires_at: str = Field(..., title="Expires At", description="Container expiration timestamp")
    days_to_live: int = Field(..., title="Days to Live", description="Container lifespan in days")
    status: str = Field(..., title="Status", description="Current container status")

class ContainerListResponse(BaseModel):
    containers: List[ContainerResponse] = Field(..., title="Containers", description="List of managed containers")
    total: int = Field(..., title="Total Count", description="Total number of containers")

class ApiResponse(BaseModel):
    success: bool = Field(..., title="Success", description="Whether the operation was successful")
    message: str = Field(..., title="Message", description="Operation result message")
    data: Optional[dict] = Field(None, title="Data", description="Additional response data")

class ContainerActionRequest(BaseModel):
    container_name: str = Field(
        ..., 
        title="Container Name",
        description="Name of the container to act upon",
        example="student123-1697123456"
    )
    
class HealthCheckResponse(BaseModel):
    status: str = Field(..., title="Status", description="Overall system health status")
    timestamp: datetime = Field(..., title="Timestamp", description="Health check timestamp")
    version: str = Field(default="1.0.0", title="Version", description="API version")
    services: dict = Field(..., title="Services", description="Status of system services")

class ErrorResponse(BaseModel):
    error: str = Field(..., title="Error", description="Error message")
    detail: Optional[str] = Field(None, title="Detail", description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.now, title="Timestamp", description="Error timestamp")

class WebContainerCreateRequest(BaseModel):
    student_name: str = Field(..., min_length=2, title="Student Name", description="Full name of the student")
    email: EmailStr = Field(..., title="Email", description="Student email address")
    purpose: str = Field(..., min_length=10, title="Purpose", description="Purpose of the container")
    storage: str = Field(default="50GB", title="Storage", description="Storage requirement")
    ram: str = Field(default="4GB", title="RAM", description="RAM requirement")
    gpu_vram: str = Field(..., title="GPU VRAM", description="GPU VRAM requirement")
    username: str = Field(..., title="Linux Username", description="Auto-generated Linux username")
    container_name: str = Field(..., title="Container Name", description="Auto-generated container name")
    days_to_live: int = Field(default=7, ge=1, le=365, title="Days to Live", description="Time period needed")
    freeze_after_days: int = Field(..., title="Freeze After", description="Freeze container after these many days")
    delete_after_days: int = Field(default=30, ge=1, title="Delete After", description="Delete container after these many days")
    send_credentials: bool = Field(default=True, title="Send Credentials", description="Send credentials to email")
    credentials_email: EmailStr = Field(..., title="Credentials Email", description="Email to send credentials to")
    
    @validator('storage')
    def validate_storage(cls, v):
        if not re.match(r'^\d+(\.\d+)?(MB|GB|TB)$', v):
            raise ValueError('Storage must be in format like "50GB" or "1TB"')
        return v
    
    @validator('ram')
    def validate_ram(cls, v):
        if not re.match(r'^\d+(\.\d+)?(MB|GB)$', v):
            raise ValueError('RAM must be in format like "4GB" or "512MB"')
        return v
    
    @validator('gpu_vram')
    def validate_gpu_vram(cls, v):
        if not re.match(r'^\d+(\.\d+)?(MB|GB)$', v):
            raise ValueError('GPU VRAM must be in format like "8GB" or "16GB"')
        return v

# Example schemas for documentation
class ContainerCreateExample:
    basic = {
        "summary": "Basic Container",
        "description": "Create a basic container with default settings",
        "value": {
            "username": "john",
            "password": "MySecure123",
            "ram": "1GB",
            "storage": "10GB",
            "student_email": "john.doe@spit.ac.in",
            "days_to_live": 7
        }
    }
    
    advanced = {
        "summary": "High-Performance Container",
        "description": "Create a container with more resources for development work",
        "value": {
            "username": "developer",
            "password": "DevPass456",
            "ram": "4GB", 
            "storage": "50GB",
            "student_email": "dev.student@spit.ac.in",
            "days_to_live": 30
        }
    }
    
    minimal = {
        "summary": "Minimal Container",
        "description": "Create a lightweight container for basic tasks",
        "value": {
            "username": "testuser",
            "password": "Test1234",
            "ram": "512MB",
            "storage": "5GB", 
            "student_email": "test@spit.ac.in",
            "days_to_live": 3
        }
    }
