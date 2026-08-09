import re
import logging
import subprocess
from typing import List, Dict
import shlex
from functools import wraps
from fastapi import HTTPException
import secrets
import string

logger = logging.getLogger(__name__)

class SecurityManager:
    """Security utilities for safe command execution and validation"""
    
    ALLOWED_COMMANDS = [
        "incus", "launch", "info", "exec", "stop", "delete", "freeze"
    ]
    
    DANGEROUS_PATTERNS = [
        r'[;&|`$()]',  # Command injection patterns
        r'\.\.',       # Directory traversal
        r'/etc/',      # System file access
        r'/proc/',     # Process information
        r'/sys/',      # System information
        r'rm\s+-rf',   # Dangerous rm commands
        r'sudo\s+rm',  # Dangerous sudo rm
        r'mkfs',       # Format commands
        r'dd\s+if',    # dd commands
        r'>/dev/',     # Device access
    ]
    
    @staticmethod
    def sanitize_username(username: str) -> str:
        """Sanitize username for safe use in commands"""
        # Only allow alphanumeric characters, hyphens, and underscores
        if not re.match(r'^[a-z][a-z0-9_-]*$', username):
            raise ValueError("Invalid username format")
        
        # Prevent reserved usernames
        reserved_names = ['root', 'admin', 'administrator', 'guest', 'daemon', 'sys', 'sync']
        if username.lower() in reserved_names:
            raise ValueError("Username not allowed")
        
        return username
    
    @staticmethod
    def sanitize_container_name(name: str) -> str:
        """Sanitize container name"""
        if not re.match(r'^[a-z][a-z0-9_-]*$', name):
            raise ValueError("Invalid container name format")
        return name
    
    @staticmethod
    def validate_resource_limits(ram: str, storage: str) -> tuple:
        """Validate and normalize resource limits"""
        # Validate RAM
        ram_match = re.match(r'^(\d+(?:\.\d+)?)(MB|GB)$', ram)
        if not ram_match:
            raise ValueError("Invalid RAM format")
        
        ram_value, ram_unit = ram_match.groups()
        ram_value = float(ram_value)
        
        # Set reasonable limits
        if ram_unit == "MB" and (ram_value < 512 or ram_value > 8192):
            raise ValueError("RAM must be between 512MB and 8GB")
        elif ram_unit == "GB" and (ram_value < 0.5 or ram_value > 8):
            raise ValueError("RAM must be between 0.5GB and 8GB")
        
        # Validate Storage
        storage_match = re.match(r'^(\d+(?:\.\d+)?)(MB|GB|TB)$', storage)
        if not storage_match:
            raise ValueError("Invalid storage format")
        
        storage_value, storage_unit = storage_match.groups()
        storage_value = float(storage_value)
        
        # Set reasonable limits
        if storage_unit == "MB" and (storage_value < 1024 or storage_value > 102400):
            raise ValueError("Storage must be between 1GB and 100GB")
        elif storage_unit == "GB" and (storage_value < 1 or storage_value > 100):
            raise ValueError("Storage must be between 1GB and 100GB")
        elif storage_unit == "TB" and storage_value > 1:
            raise ValueError("Storage cannot exceed 1TB")
        
        return ram, storage
    
    @staticmethod
    def safe_command_execution(cmd_parts: List[str], allowed_commands: List[str] = None) -> subprocess.CompletedProcess:
        """Safely execute commands with validation"""
        if not cmd_parts:
            raise ValueError("Empty command")
        
        # Use default allowed commands if none provided
        if allowed_commands is None:
            allowed_commands = SecurityManager.ALLOWED_COMMANDS
        
        # Check if command is allowed
        base_command = cmd_parts[0]
        if base_command not in allowed_commands:
            raise ValueError(f"Command '{base_command}' not allowed")
        
        # Check for dangerous patterns
        full_command = " ".join(cmd_parts)
        for pattern in SecurityManager.DANGEROUS_PATTERNS:
            if re.search(pattern, full_command):
                raise ValueError(f"Dangerous pattern detected in command")
        
        # Log the command for audit
        logger.info(f"Executing safe command: {full_command}")
        
        try:
            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                check=False,  # Don't raise exception on non-zero exit
                timeout=300   # 5 minute timeout
            )
            return result
        except subprocess.TimeoutExpired:
            raise ValueError("Command timed out")
        except Exception as e:
            logger.error(f"Command execution error: {str(e)}")
            raise ValueError(f"Command execution failed: {str(e)}")
    
    @staticmethod
    def generate_secure_password(length: int = 16) -> str:
        """Generate a secure random password"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def validate_email_domain(email: str, allowed_domains: List[str] = None) -> bool:
        """Validate email domain if restrictions are needed"""
        if allowed_domains is None:
            return True
        
        domain = email.split('@')[1] if '@' in email else ''
        return domain.lower() in [d.lower() for d in allowed_domains]
    
    @staticmethod
    def rate_limit_check(user_id: str, max_requests: int = 5, window_minutes: int = 60) -> bool:
        """Simple rate limiting (in-memory, for demo purposes)"""
        # In production, use Redis or database for rate limiting
        # This is a simplified version
        return True  # Allow all for now
    
    @staticmethod
    def sanitize_file_path(path: str, base_dir: str = "/tmp") -> str:
        """Sanitize file paths to prevent directory traversal"""
        # Remove any path traversal attempts
        path = path.replace('..', '').replace('//', '/')
        
        # Ensure path is within base directory
        if not path.startswith(base_dir):
            path = f"{base_dir}/{path.lstrip('/')}"
        
        return path

def require_admin(func):
    """Decorator to require admin privileges for certain endpoints"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # In production, implement proper admin authentication
        # For now, this is a placeholder
        return await func(*args, **kwargs)
    return wrapper

def validate_input(func):
    """Decorator to validate input parameters"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            raise HTTPException(status_code=500, detail="Validation failed")
    return wrapper
