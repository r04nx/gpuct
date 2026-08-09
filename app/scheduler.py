import schedule
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List
from app.container_manager import ContainerManager
from app.email_service import EmailService
import threading
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContainerScheduler:
    def __init__(self):
        self.container_manager = ContainerManager()
        self.email_service = EmailService()
        self.running = False
        
    async def check_expired_containers(self):
        """Check for expired containers and freeze them"""
        try:
            logger.info("Checking for expired containers...")
            await self.container_manager.cleanup_expired_containers()
            logger.info("Expired containers check completed")
        except Exception as e:
            logger.error(f"Error in expired containers check: {str(e)}")
    
    async def send_expiration_warnings(self):
        """Send warning emails for containers expiring soon"""
        try:
            logger.info("Checking for containers expiring soon...")
            containers = await self.container_manager.list_containers()
            current_time = datetime.now()
            
            for container in containers:
                if container['status'] != 'running':
                    continue
                    
                expiration_time = datetime.fromisoformat(container['expires_at'])
                time_remaining = expiration_time - current_time
                days_remaining = time_remaining.days
                
                # Send warning 3 days and 1 day before expiration
                if days_remaining in [3, 1] and time_remaining.seconds < 3600:
                    logger.info(f"Sending expiration warning for {container['name']} ({days_remaining} days remaining)")
                    await self.email_service.send_expiration_warning(container, days_remaining)
                    
        except Exception as e:
            logger.error(f"Error in expiration warnings: {str(e)}")
    
    def run_sync_task(self, async_func):
        """Run async function in sync context"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(async_func())
            loop.close()
        except Exception as e:
            logger.error(f"Error in sync task: {str(e)}")
    
    def start_scheduler(self):
        """Start the scheduler"""
        logger.info("Starting container scheduler...")
        
        # Schedule tasks
        schedule.every().hour.do(lambda: self.run_sync_task(self.check_expired_containers))
        schedule.every().day.at("09:00").do(lambda: self.run_sync_task(self.send_expiration_warnings))
        schedule.every().day.at("18:00").do(lambda: self.run_sync_task(self.send_expiration_warnings))
        
        self.running = True
        
        def run_scheduler():
            while self.running:
                schedule.run_pending()
                time.sleep(60)
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        logger.info("Container scheduler started successfully")
        return scheduler_thread
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        logger.info("Stopping container scheduler...")
        self.running = False
        schedule.clear()

scheduler = ContainerScheduler()

def start_background_scheduler():
    return scheduler.start_scheduler()

def stop_background_scheduler():
    scheduler.stop_scheduler()
