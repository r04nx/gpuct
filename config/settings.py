import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Email configuration
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "mac4@spit.ac.in"
    
    # Container configuration
    DEFAULT_RAM: str = "1GB"
    DEFAULT_STORAGE: str = "10GB"
    DEFAULT_IMAGE: str = "ubuntu:22.04"
    
    # Network configuration
    NETWORK_RANGE: str = "10.10.0.0/16"
    
    # SSH configuration
    SSH_KEY_TYPE: str = "rsa"
    SSH_KEY_SIZE: int = 2048
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "../logs/gpuct.log"
    
    # Database (for container tracking)
    DATABASE_URL: Optional[str] = None
    
    class Config:
        env_file = "../.env"
        case_sensitive = True

settings = Settings()
