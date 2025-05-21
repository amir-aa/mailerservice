import pytest
import json
from unittest.mock import MagicMock, patch, ANY
from datetime import datetime
from peewee import DoesNotExist

from services.email_service import EmailService, EmailSender
from models.email_model import EmailMessage
from models.smtp_config import SmtpConfig

class TestEmailService:
    def test_create_email(self, db, smtp_config, email_service):
        """Test creating an email"""
        recipients = ["recipient@example.com"]
        html_content = "<p>Test content</p>"
        
        email_id = email_service.create_email(
            subject="Test Subject",
            recipients=recipients,
            html_content=html_content,
            smtp_config_id=smtp_config.id,
            priority=2
        )
        
        # Verify email was created in database
        email = EmailMessage.get_by_id(email_id)
        assert email.subject == "Test Subject"
        assert json.loads(email.recipients) == recipients
        assert email.html_content == html_content
        assert email.status == "queued"
        assert email.priority == 2
        
        # Verify email was added to queue
        email_service.queue_service.enqueue.assert_called_once_with(email_id, 2)
    
    def test_create_email_auto_select_smtp(self, db, smtp_config, email_service):
        """Test creating an email with automatic SMTP selection"""
        # Create email without specifying SMTP config
        email_id = email_service.create_email(
            subject="Test Subject",
            recipients=["recipient@example.com"],
            html_content="<p>Test content</p>"
        )
        
        # Verify email was created with the available SMTP config
        email = EmailMessage.get_by_id(email_id)
        assert email.smtp_config_id == smtp_config.id
    
    @patch('services.email_service.EmailSender.send_email')
    def test_process_queued_email(self, mock_send, db, test_email, email_service):
        """Test processing a queued email"""
        # Configure mock to return success
        mock_send.return_value = (True, "Success")
        
        # Process the email
        result = email_service.process_queued_email(test_email.id)
        
        # Verify result
        assert result is True
        mock_send.assert_called_once_with(test_email.id)
    
    def test_handle_failed_email_retry(self, db, test_email, email_service):
        """Test handling a failed email with retry"""
        # Set max retries
        max_retries = 3
        
        # Handle failed email
        email_service.handle_failed_email(test_email.id, max_retries)
        
        # Verify email was updated
        test_email.refresh()
        assert test_email.retry_count == 1
        
        # Verify email was requeued
        email_service.queue_service.enqueue.assert_called_with(test_email.id, ANY)
    
    def test_handle_failed_email_max_retries(self, db, test_email, email_service):
        """Test handling a failed email at max retries"""
        # Set retry count to max
        test_email.retry_count = 3
        test_email.save()
        
        # Handle failed email
        email_service.handle_failed_email(test_email.id, 3)
        
        # Verify email was marked as permanently failed
        test_email.refresh()
        assert test_email.status == "failed"
        assert "Maximum retry attempts" in test_email.error_message
        
        # Verify email was not requeued
        email_service.queue_service.enqueue.assert_not_called()
    
    def test_get_best_smtp_config(self, db, smtp_config, email_service):
        """Test getting the best SMTP configuration"""
        # Create another config with higher utilization
        high_usage_config = SmtpConfig.create(
            name="High Usage SMTP",
            email_address="high@example.com",
            smtp_host="smtp.high.com",
            smtp_port=587,
            username="high@example.com",
            password="password",
            active=True,
            daily_limit=100,
            hourly_limit=10,
            sent_count_today=80  # 80% utilization
        )
        
        # Get best config (should be the one with lower utilization)
        best_config = email_service._get_best_smtp_config()
        assert best_config.id == smtp_config.id
        
        # Test with exclusion
        best_config_excluding = email_service._get_best_smtp_config(exclude_id=smtp_config.id)
        assert best_config_excluding.id == high_usage_config.id
        
        # Test when no configs available
        smtp_config.active = False
        smtp_config.save()
        high_usage_config.active = False
        high_usage_config.save()
        
        no_config = email_service._get_best_smtp_config()
        assert no_config is None


class TestEmailSender:
    @patch('smtplib.SMTP')
    def test_send_email_success(self, mock_smtp, db, test_email, smtp_config):
        """Test successfully sending an email"""
        # Setup mock SMTP instance
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_smtp_instance
        
        # Call the send_email method
        success, message = EmailSender.send_email(test_email.id)
        
        # Verify email was sent
        assert success is True
        assert "successfully" in message
        mock_smtp_instance.login.assert_called_once()
        mock_smtp_instance.sendmail.assert_called_once()
        
        # Verify email status was updated
        test_email.refresh()
        assert test_email.status == "sent"
        assert test_email.sent_at is not None
        
        # Verify SMTP config counters were updated
        smtp_config.refresh()
        assert smtp_config.sent_count_today == 1
        assert smtp_config.sent_count_hour == 1
    
    @patch('smtplib.SMTP')
    def test_send_email_failure(self, mock_smtp, db, test_email, smtp_config):
        """Test failure when sending an email"""
        # Setup mock to raise an exception
        mock_smtp.return_value.__enter__.side_effect = Exception("SMTP error")
        
        # Call the send_email method
        success, message = EmailSender.send_email(test_email.id)
        
        # Verify result
        assert success is False
        assert "SMTP error" in message
        
        # Verify email status was updated
        test_email.refresh()
        assert test_email.status == "failed"
        assert test_email.error_message == "SMTP error"
        
        # Verify SMTP config counters were not updated
        smtp_config.refresh()
        assert smtp_config.sent_count_today == 0
        assert smtp_config.sent_count_hour == 0