import queue
import threading
import time
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('queue_service')

class EmailQueue:
    """Email queue manager for congestion control"""
    
    def __init__(self, worker_count=2, max_retries=3):
        self.queue = queue.PriorityQueue()
        self.worker_count = worker_count
        self.max_retries = max_retries
        self.workers = []
        self.running = False
        self.email_service = None  # Will be set after initialization
    
    def set_email_service(self, email_service):
        """Set the email service to use for sending emails"""
        self.email_service = email_service
    
    def enqueue(self, email_id: int, priority: int = 1):
        """Add an email to the queue with priority (1=highest, 5=lowest)"""
        self.queue.put((priority, email_id))
        logger.info(f"Email {email_id} added to queue with priority {priority}")
    
    def start_workers(self):
        """Start worker threads to process the queue"""
        if self.running:
            return
            
        if not self.email_service:
            raise ValueError("Email service not set")
            
        self.running = True
        
        for i in range(self.worker_count):
            worker = threading.Thread(target=self._worker_process, args=(i,))
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
            
        logger.info(f"Started {self.worker_count} worker threads")
    
    def stop_workers(self):
        """Stop all worker threads"""
        self.running = False
        # Wait for all workers to finish
        for worker in self.workers:
            if worker.is_alive():
                worker.join(timeout=5.0)
        self.workers = []
        logger.info("All worker threads stopped")
    
    def _worker_process(self, worker_id: int):
        """Worker process to send emails from the queue"""
        logger.info(f"Worker {worker_id} started")
        
        while self.running:
            try:
                # Get email from queue with 1-second timeout
                try:
                    priority, email_id = self.queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                logger.info(f"Worker {worker_id} processing email {email_id} (priority: {priority})")
                
                # Process the email
                success = self.email_service.process_queued_email(email_id)
                
                if not success:
                    # If failed, check retry count and possibly requeue
                    self.email_service.handle_failed_email(email_id, self.max_retries)
                
                # Mark task as done
                self.queue.task_done()
                
            except Exception as e:
                logger.error(f"Worker {worker_id} encountered an error: {str(e)}")
                # Sleep a bit before continuing to prevent tight loops on errors
                time.sleep(1)
        
        logger.info(f"Worker {worker_id} stopped")