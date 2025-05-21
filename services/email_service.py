import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import threading
import logging
from peewee import DoesNotExist, fn

from models.email_model import EmailMessage, db
from models.smtp_config import SmtpConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('email_service')

class EmailSender:
    """Email sending service using SMTP"""
    
    @staticmethod
    def send_email(email_id: int) -> Tuple[bool, str]:
        """Send an email by ID from the database"""
        try:
            with db.atomic():
                # Get email from database
                email = EmailMessage.get_by_id(email_id)
                
                if email.status == 'sent':
                    return True, "Email already sent"
                
                # Get SMTP configuration
                smtp_config = SmtpConfig.get_by_id(email.smtp_config_id)
                
                if not smtp_config.active:
                    return False, "SMTP configuration is inactive"
                
                if not smtp_config.can_send():
                    return False, "SMTP sending limits reached"
                
                # Update email status to sending
                email.update_status('sending')
                
                # Create message
                msg = MIMEMultipart('alternative')
                msg['Subject'] = email.subject
                
                # Set sender with display name if available
                if smtp_config.display_name:
                    msg['From'] = f"{smtp_config.display_name} <{smtp_config.email_address}>"
                else:
                    msg['From'] = smtp_config.email_address
                
                # Set recipients
                recipients_list = email.get_recipients_list()
                msg['To'] = ', '.join(recipients_list)
                
                # Set CC if available
                cc_list = email.get_cc_list()
                if cc_list:
                    msg['Cc'] = ', '.join(cc_list)
                
                # Get BCC list if available
                bcc_list = email.get_bcc_list()
                
                # Attach HTML content
                html_part = MIMEText(email.html_content, 'html')
                msg.attach(html_part)
                
                # Get all recipients for sending
                all_recipients = recipients_list + cc_list + bcc_list
                
                # Connect to SMTP server and send
                if smtp_config.use_ssl:
                    server = smtplib.SMTP_SSL(smtp_config.smtp_host, smtp_config.smtp_port)
                else:
                    server = smtplib.SMTP(smtp_config.smtp_host, smtp_config.smtp_port)
                    
                    if smtp_config.use_tls:
                        server.starttls()
                
                server.login(smtp_config.username, smtp_config.password)
                server.sendmail(smtp_config.email_address, all_recipients, msg.as_string())
                server.quit()
                
                # Update email status and SMTP counters
                email.update_status('sent')
                smtp_config.increment_sent_count()
                
                return True, "Email sent successfully"
                
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error sending email {email_id}: {error_message}")
            
            # Update email status to failed
            try:
                with db.atomic():
                    email = EmailMessage.get_by_id(email_id)
                    email.update_status('failed', error_message)
            except Exception as update_error:
                logger.error(f"Error updating email status: {str(update_error)}")
                
            return False, error_message


class EmailService:
    """Service for managing emails"""
    
    def __init__(self, queue_service=None):
        self.queue_service = queue_service
        
        # If queue service provided, set this service as its email service
        if queue_service:
            queue_service.set_email_service(self)
    
    def create_email(self, subject: str, recipients: List[str], 
                    html_content: str, smtp_config_id: int = None,
                    cc: Optional[List[str]] = None, 
                    bcc: Optional[List[str]] = None,
                    priority: int = 1) -> int:
        """Create a new email in the database"""
        
        # If no SMTP config provided, get the best available one
        if smtp_config_id is None:
            smtp_config = self._get_best_smtp_config()
            if not smtp_config:
                raise ValueError("No available SMTP configuration found")
            smtp_config_id = smtp_config.id
        
        with db.atomic():
            email = EmailMessage.create(
                subject=subject,
                sender="",  # Will be determined by SMTP config
                recipients=json.dumps(recipients),
                cc=json.dumps(cc) if cc else None,
                bcc=json.dumps(bcc) if bcc else None,
                html_content=html_content,
                status='queued',
                smtp_config_id=smtp_config_id,
                priority=priority
            )
            
            # Add to queue if queue service is available
            if self.queue_service:
                self.queue_service.enqueue(email.id, priority)
            
            return email.id
    
    def process_queued_email(self, email_id: int) -> bool:
        """Process an email from the queue"""
        success, message = EmailSender.send_email(email_id)
        logger.info(f"Email {email_id} processed: {'Success' if success else 'Failed'} - {message}")
        return success
    
    def handle_failed_email(self, email_id: int, max_retries: int) -> None:
        """Handle a failed email, potentially requeuing it"""
        try:
            with db.atomic():
                email = EmailMessage.get_by_id(email_id)
                
                # If we haven't exceeded max retries, requeue with lower priority
                if email.retry_count < max_retries:
                    email.increment_retry()
                    new_priority = min(5, email.priority + 1)  # Decrease priority (higher number)
                    
                    # Try a different SMTP config if available
                    new_smtp_config = self._get_best_smtp_config(exclude_id=email.smtp_config_id)
                    if new_smtp_config:
                        email.smtp_config_id = new_smtp_config.id
                        email.save()
                    
                    # Requeue with new priority
                    if self.queue_service:
                        self.queue_service.enqueue(email.id, new_priority)
                        logger.info(f"Email {email_id} requeued with priority {new_priority}, retry {email.retry_count}")
                else:
                    # Mark as permanently failed
                    email.update_status('failed', "Maximum retry attempts exceeded")
                    logger.info(f"Email {email_id} permanently failed after {max_retries} retries")
        except Exception as e:
            logger.error(f"Error handling failed email {email_id}: {str(e)}")
    
    def get_email(self, email_id: int) -> Dict[str, Any]:
        """Get email details by ID"""
        with db.atomic():
            email = EmailMessage.get_by_id(email_id)
            smtp_config = SmtpConfig.get_by_id(email.smtp_config_id)
            
            return {
                'id': email.id,
                'subject': email.subject,
                'sender': smtp_config.email_address,
                'sender_name': smtp_config.display_name,
                'recipients': email.get_recipients_list(),
                'cc': email.get_cc_list(),
                'bcc': email.get_bcc_list(),
                'status': email.status,
                'priority': email.priority,
                'retry_count': email.retry_count,
                'smtp_config': smtp_config.name,
                'created_at': email.created_at.isoformat(),
                'updated_at': email.updated_at.isoformat(),
                'sent_at': email.sent_at.isoformat() if email.sent_at else None,
                'error_message': email.error_message
            }
    
    def get_emails_by_status(self, status: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get emails by status"""
        with db.atomic():
            emails = EmailMessage.select().where(EmailMessage.status == status).limit(limit)
            return [{
                'id': email.id,
                'subject': email.subject,
                'status': email.status,
                'priority': email.priority,
                'retry_count': email.retry_count,
                'created_at': email.created_at.isoformat()
            } for email in emails]
    
    def _get_best_smtp_config(self, exclude_id=None) -> Optional[SmtpConfig]:
        """Get the best available SMTP configuration"""
        query = (
            SmtpConfig
            .select()
            .where(
                (SmtpConfig.active == True) & 
                (SmtpConfig.sent_count_today < SmtpConfig.daily_limit) &
                (SmtpConfig.sent_count_hour < SmtpConfig.hourly_limit)
            )
        )
        
        if exclude_id is not None:
            query = query.where(SmtpConfig.id != exclude_id)
        
        # Order by utilization (lowest first)
        query = query.order_by(
            fn.CAST(SmtpConfig.sent_count_today, 'FLOAT') / fn.CAST(SmtpConfig.daily_limit, 'FLOAT')
        )
        
        try:
            return query.get()
        except DoesNotExist:
            return None
    
    def create_smtp_config(self, **kwargs) -> int:
        """Create a new SMTP configuration"""
        with db.atomic():
            smtp_config = SmtpConfig.create(**kwargs)
            return smtp_config.id
    
    def update_smtp_config(self, config_id: int, **kwargs) -> bool:
        """Update an SMTP configuration"""
        try:
            with db.atomic():
                smtp_config = SmtpConfig.get_by_id(config_id)
                
                for key, value in kwargs.items():
                    if hasattr(smtp_config, key):
                        setattr(smtp_config, key, value)
                
                smtp_config.updated_at = datetime.now()
                smtp_config.save()
                return True
        except Exception:
            return False
    
    def get_smtp_config(self, config_id: int) -> Dict[str, Any]:
        """Get SMTP configuration details"""
        with db.atomic():
            config = SmtpConfig.get_by_id(config_id)
            return {
                'id': config.id,
                'name': config.name,
                'email_address': config.email_address,
                'display_name': config.display_name,
                'smtp_host': config.smtp_host,
                'smtp_port': config.smtp_port,
                'username': config.username,
                'active': config.active,
                'daily_limit': config.daily_limit,
                'hourly_limit': config.hourly_limit,
                'sent_count_today': config.sent_count_today,
                'sent_count_hour': config.sent_count_hour,
                'last_sent': config.last_sent.isoformat() if config.last_sent else None,
                'created_at': config.created_at.isoformat()
            }
    
    def list_smtp_configs(self) -> List[Dict[str, Any]]:
        """List all SMTP configurations"""
        with db.atomic():
            configs = SmtpConfig.select()
            return [{
                'id': config.id,
                'name': config.name,
                'email_address': config.email_address,
                'active': config.active,
                'daily_limit': config.daily_limit,
                'sent_count_today': config.sent_count_today,
                'sent_count_hour': config.sent_count_hour
            } for config in configs]