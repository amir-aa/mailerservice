import pytest
import json
from datetime import datetime, timedelta
from models.email_model import EmailMessage
from models.smtp_config import SmtpConfig

class TestEmailMessage:
    def test_create_email(self, db, smtp_config):
        """Test creating an email message"""
        recipients = ["test@example.com", "another@example.com"]
        cc = ["cc@example.com"]
        bcc = ["bcc@example.com"]
        
        email = EmailMessage.create(
            subject="Test Subject",
            sender="sender@example.com",
            recipients=json.dumps(recipients),
            cc=json.dumps(cc),
            bcc=json.dumps(bcc),
            html_content="<p>Test content</p>",
            status="queued",
            smtp_config_id=smtp_config.id,
            priority=1
        )
        
        assert email.id is not None
        assert email.subject == "Test Subject"
        assert email.status == "queued"
        assert email.priority == 1
        assert email.retry_count == 0
        
        # Test the list conversion methods
        assert email.get_recipients_list() == recipients
        assert email.get_cc_list() == cc
        assert email.get_bcc_list() == bcc
    
    def test_update_status(self, db, test_email):
        """Test updating email status"""
        test_email.update_status("sending")
        assert test_email.status == "sending"
        assert test_email.error_message is None
        
        # Test marking as sent
        test_email.update_status("sent")
        assert test_email.status == "sent"
        assert test_email.sent_at is not None
        
        # Test marking as failed
        error_msg = "SMTP connection failed"
        test_email.update_status("failed", error_msg)
        assert test_email.status == "failed"
        assert test_email.error_message == error_msg
    
    def test_increment_retry(self, db, test_email):
        """Test incrementing retry count"""
        assert test_email.retry_count == 0
        
        test_email.increment_retry()
        assert test_email.retry_count == 1
        
        test_email.increment_retry()
        assert test_email.retry_count == 2


class TestSmtpConfig:
    def test_create_smtp_config(self, db):
        """Test creating an SMTP configuration"""
        config = SmtpConfig.create(
            name="Test SMTP",
            email_address="test@example.com",
            display_name="Test Sender",
            smtp_host="smtp.example.com",
            smtp_port=587,
            username="test@example.com",
            password="password123",
            use_tls=True,
            active=True,
            daily_limit=100,
            hourly_limit=10
        )
        
        assert config.id is not None
        assert config.name == "Test SMTP"
        assert config.email_address == "test@example.com"
        assert config.smtp_port == 587
        assert config.active is True
        assert config.sent_count_today == 0
        assert config.sent_count_hour == 0
    
    def test_can_send(self, db, smtp_config):
        """Test checking if SMTP config can send"""
        # Initially should be able to send
        assert smtp_config.can_send() is True
        
        # Test when inactive
        smtp_config.active = False
        smtp_config.save()
        assert smtp_config.can_send() is False
        
        # Test when at daily limit
        smtp_config.active = True
        smtp_config.sent_count_today = smtp_config.daily_limit
        smtp_config.save()
        assert smtp_config.can_send() is False
        
        # Test when at hourly limit
        smtp_config.sent_count_today = 0
        smtp_config.sent_count_hour = smtp_config.hourly_limit
        smtp_config.save()
        assert smtp_config.can_send() is False
    
    def test_increment_sent_count(self, db, smtp_config):
        """Test incrementing sent counts"""
        assert smtp_config.sent_count_today == 0
        assert smtp_config.sent_count_hour == 0
        
        smtp_config.increment_sent_count()
        assert smtp_config.sent_count_today == 1
        assert smtp_config.sent_count_hour == 1
        assert smtp_config.last_sent is not None
    
    def test_reset_counters(self, db, smtp_config):
        """Test resetting counters"""
        # Set some counts
        smtp_config.sent_count_today = 50
        smtp_config.sent_count_hour = 5
        
        # Set last reset times to yesterday and 2 hours ago
        yesterday = datetime.now() - timedelta(days=1)
        two_hours_ago = datetime.now() - timedelta(hours=2)
        
        smtp_config.last_reset_daily = yesterday
        smtp_config.last_reset_hourly = two_hours_ago
        smtp_config.save()
        
        # Call method that should reset counters
        now = datetime.now()
        smtp_config._reset_counters(now)
        
        # Verify counters were reset
        assert smtp_config.sent_count_today == 0
        assert smtp_config.sent_count_hour == 0
        assert smtp_config.last_reset_daily > yesterday
        assert smtp_config.last_reset_hourly > two_hours_ago