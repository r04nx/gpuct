import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict
import logging
from jinja2 import Template
from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.username = settings.SMTP_USERNAME
        self.password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL
    
    async def send_container_notification(self, container_info: Dict) -> bool:
        """
        Send email notification with container details and SSH key
        """
        try:
            # Create message container
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = container_info['student_email']
            msg['Subject'] = f"Your Ubuntu Container is Ready - {container_info['name']}"
            
            # Create email body
            body = self._generate_email_body(container_info)
            msg.attach(MIMEText(body, 'html'))
            
            # Attach private key file
            if 'private_key_file' in container_info:
                self._attach_private_key(msg, container_info)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            text = msg.as_string()
            server.sendmail(self.from_email, container_info['student_email'], text)
            server.quit()
            
            logger.info(f"Email sent successfully to {container_info['student_email']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def _generate_email_body(self, container_info: Dict) -> str:
        """Generate HTML email body with container details and SSH instructions"""
        
        email_template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; color: #333; }
                .header { background-color: #4CAF50; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; }
                .info-box { background-color: #f9f9f9; border: 1px solid #ddd; padding: 15px; margin: 10px 0; }
                .command { background-color: #f4f4f4; border-left: 4px solid #4CAF50; padding: 10px; font-family: monospace; margin: 10px 0; }
                .warning { background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; margin: 10px 0; }
                .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎉 Your Ubuntu Container is Ready!</h1>
            </div>
            
            <div class="content">
                <p>Dear Student,</p>
                
                <p>Your Ubuntu container has been successfully created and is ready for use. Below are the connection details and instructions:</p>
                
                <div class="info-box">
                    <h3>Container Information</h3>
                    <ul>
                        <li><strong>Container Name:</strong> {{ container_name }}</li>
                        <li><strong>Username:</strong> {{ username }}</li>
                        <li><strong>IP Address:</strong> {{ ip_address }}</li>
                        <li><strong>Created:</strong> {{ created_at }}</li>
                        <li><strong>Expires:</strong> {{ expires_at }} ({{ days_to_live }} days)</li>
                    </ul>
                </div>
                
                <h3>🔐 SSH Connection Instructions</h3>
                
                <p>A private SSH key has been attached to this email (<strong>{{ username }}-{{ container_name }}.pem</strong>). Follow these steps to connect:</p>
                
                <h4>Step 1: Save and Set Permissions for SSH Key</h4>
                <div class="command">
                    # Save the attached key file to your local machine<br>
                    # Then set proper permissions:<br>
                    chmod 600 {{ username }}-{{ container_name }}.pem
                </div>
                
                <h4>Step 2: Connect via SSH</h4>
                <div class="command">
                    ssh -i {{ username }}-{{ container_name }}.pem {{ username }}@{{ ip_address }}
                </div>
                
                <h4>Alternative: SSH with Password (if key doesn't work)</h4>
                <div class="command">
                    ssh {{ username }}@{{ ip_address }}
                    # Use the password you provided during container creation
                </div>
                
                <h4>Step 3: Test Your Connection</h4>
                <div class="command">
                    # Once connected, try these commands:<br>
                    whoami<br>
                    pwd<br>
                    ls -la<br>
                    sudo apt update
                </div>
                
                <div class="warning">
                    <strong>⚠️ Important Notes:</strong>
                    <ul>
                        <li>Keep your SSH private key secure and do not share it</li>
                        <li>This container will be automatically frozen after {{ days_to_live }} days</li>
                        <li>Make sure to backup your work before the expiration date</li>
                        <li>You have sudo access in the container</li>
                    </ul>
                </div>
                
                <h3>📚 Common Tasks</h3>
                <p>Here are some common commands you might need:</p>
                <div class="command">
                    # Update system packages<br>
                    sudo apt update && sudo apt upgrade<br><br>
                    
                    # Install development tools<br>
                    sudo apt install build-essential git vim nano<br><br>
                    
                    # Check system resources<br>
                    free -h    # Memory usage<br>
                    df -h      # Disk usage<br>
                    top        # Running processes
                </div>
                
                <h3>🆘 Need Help?</h3>
                <p>If you encounter any issues connecting to your container, please contact the system administrator.</p>
                
                <p>Happy coding!</p>
            </div>
            
            <div class="footer">
                <p>This email was automatically generated by the SPIT-CTF Container Management System.<br>
                Container created on {{ created_at }}</p>
            </div>
        </body>
        </html>
        """)
        
        return email_template.render(
            container_name=container_info['name'],
            username=container_info['username'],
            ip_address=container_info['ip_address'],
            created_at=container_info['created_at'],
            expires_at=container_info['expires_at'],
            days_to_live=container_info['days_to_live']
        )
    
    def _attach_private_key(self, msg: MIMEMultipart, container_info: Dict):
        """Attach private key file to email"""
        try:
            key_file_path = container_info['private_key_file']
            if os.path.exists(key_file_path):
                with open(key_file_path, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    filename = f"{container_info['username']}-{container_info['name']}.pem"
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {filename}'
                    )
                    msg.attach(part)
                    logger.info(f"Private key attached: {filename}")
            else:
                logger.warning(f"Private key file not found: {key_file_path}")
        except Exception as e:
            logger.error(f"Failed to attach private key: {str(e)}")
    
    async def send_expiration_warning(self, container_info: Dict, days_remaining: int) -> bool:
        """Send warning email before container expiration"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = container_info['student_email']
            msg['Subject'] = f"Container Expiration Warning - {container_info['name']}"
            
            body = f"""
            <html>
            <body>
                <h2>⚠️ Container Expiration Warning</h2>
                <p>Dear Student,</p>
                <p>Your container <strong>{container_info['name']}</strong> will expire in <strong>{days_remaining} day(s)</strong>.</p>
                <p><strong>Container Details:</strong></p>
                <ul>
                    <li>Username: {container_info['username']}</li>
                    <li>IP Address: {container_info['ip_address']}</li>
                    <li>Expiration Date: {container_info['expires_at']}</li>
                </ul>
                <p>Please make sure to backup your important data before the container is frozen.</p>
                <p>Best regards,<br>SPIT-CTF Container Management System</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            text = msg.as_string()
            server.sendmail(self.from_email, container_info['student_email'], text)
            server.quit()
            
            logger.info(f"Expiration warning sent to {container_info['student_email']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send expiration warning: {str(e)}")
            return False
