import pytest
from utils.validators import validate_email_input, validate_smtp_config, is_valid_email

class TestValidators:
    def test_is_valid_email(self):
        """Test email validation function"""
        # Valid emails
        assert is_valid_email('test@example.com') is True
        assert is_valid_email('user.name+tag@example.co.uk') is True
        
        # Invalid emails
        assert is_valid_email('test@') is False
        assert is_valid_email('test@example') is False
        assert is_valid_email('test') is False
        assert is_valid_email('@example.com') is False
    
    def test_validate_email_input_success(self):
        """Test successful email input validation"""
        # Valid input
        result = validate_email_input({
            'subject': 'Test Subject',
            'recipients': ['test@example.com'],
            'html_content': '<p>Test content</p>',
            'cc': ['cc@example.com'],
            'bcc': ['bcc@example.com'],
            'priority': 2
        })
        
        assert result['valid'] is True
    
    def test_validate_email_input_missing_fields(self):
        """Test email validation with missing fields"""
        # Missing subject
        result = validate_email_input({
            'recipients': ['test@example.com'],
            'html_content': '<p>Test content</p>'
        })
        assert result['valid'] is False
        assert 'subject' in result['message']
        
        # Missing recipients
        result = validate_email_input({
            'subject': 'Test Subject',
            'html_content': '<p>Test content</p>'
        })
        assert result['valid'] is False
        assert 'recipients' in result['message']
        
        # Missing html_content
        result = validate_email_input({
            'subject': 'Test Subject',
            'recipients': ['test@example.com']
        })
        assert result['valid'] is False
        assert 'html_content' in result['message']
    
    def test_validate_email_input_invalid_recipients(self):
        """Test email validation with invalid recipients"""
        # Empty recipients list
        result = validate_email_input({
            'subject': 'Test Subject',
            'recipients': [],
            'html_content': '<p>Test content</p>'
        })
        assert result['valid'] is False
        assert 'Recipients must be a non-empty list' in result['message']
        
        # Invalid email format
        result = validate_email_input({
            'subject': 'Test Subject',
            'recipients': ['invalid-email'],
            'html_content': '<p>Test content</p>'
        })
        assert result['valid'] is False
        assert 'Invalid recipient email format' in result['message']
        
        # CC not a list
        result = validate_email_input({
            'subject': 'Test Subject',
            'recipients': ['test@example.com'],
            'html_content': '<p>Test content</p>',
            'cc': 'cc@example.com'  # Not a list
        })
        assert result['valid'] is False
        assert 'CC must be a list' in result['message']
        
        # BCC with invalid email
        result = validate_email_input({
            'subject': 'Test Subject',
            'recipients': ['test@example.com'],
            'html_content': '<p>Test content</p>',
            'bcc': ['invalid-bcc']
        })
        assert result['valid'] is False
        assert 'Invalid BCC email format' in result['message']
    
    def test_validate_email_input_invalid_priority(self):
        """Test email validation with invalid priority"""
        # Priority too low
        result = validate_email_input({
            'subject': 'Test Subject',
            'recipients': ['test@example.com'],
            'html_content': '<p>Test content</p>',
            'priority': 0  # Too low
        })
        assert result['valid'] is False
        assert 'Priority must be between 1 and 5' in result['message']
        
        # Priority too high
        result = validate_email_input({
            'subject': 'Test Subject',
            'recipients': ['test@example.com'],
            'html_content': '<p>Test content</p>',
            'priority': 6  # Too high
        })
        assert result['valid'] is False
        assert 'Priority must be between 1 and 5' in result['message']
        
        # Priority not an integer
        result = validate_email_input({
            'subject': 'Test Subject',
            'recipients': ['test@example.com'],
            'html_content': '<p>Test content</p>',
            'priority': 'high'  # Not an integer
        })
        assert result['valid'] is False
        assert 'Priority must be an integer' in result['message']
    
    def test_validate_smtp_config_success(self):
        """Test successful SMTP config validation"""
        # Valid input
        result = validate_smtp_config({
            'name': 'Test SMTP',
            'email_address': 'test@example.com',
            'smtp_host': 'smtp.example.com',
            'smtp_port': 587,
            'username': 'test@example.com',
            'password': 'password123',
            'daily_limit': 100,
            'hourly_limit': 10
        })
        
        assert result['valid'] is True
    
    def test_validate_smtp_config_missing_fields(self):
        """Test SMTP config validation with missing fields"""
        # Missing name
        result = validate_smtp_config({
            'email_address': 'test@example.com',
            'smtp_host': 'smtp.example.com',
            'smtp_port': 587,
            'username': 'test@example.com',
            'password': 'password123'
        })
        assert result['valid'] is False
        assert 'name' in result['message']
        
        # Missing password
        result = validate_smtp_config({
            'name': 'Test SMTP',
            'email_address': 'test@example.com',
            'smtp_host': 'smtp.example.com',
            'smtp_port': 587,
            'username': 'test@example.com'
            # Missing password
        })
        assert result['valid'] is False
        assert 'password' in result['message']
    
    def test_validate_smtp_config_invalid_values(self):
        """Test SMTP config validation with invalid values"""
        # Invalid email
        result = validate_smtp_config({
            'name': 'Test SMTP',
            'email_address': 'invalid-email',
            'smtp_host': 'smtp.example.com',
            'smtp_port': 587,
            'username': 'test@example.com',
            'password': 'password123'
        })
        assert result['valid'] is False
        assert 'Invalid email address format' in result['message']
        
        # Invalid port (too high)
        result = validate_smtp_config({
            'name': 'Test SMTP',
            'email_address': 'test@example.com',
            'smtp_host': 'smtp.example.com',
            'smtp_port': 70000,  # Too high
            'username': 'test@example.com',
            'password': 'password123'
        })
        assert result['valid'] is False
        assert 'SMTP port must be between 1 and 65535' in result['message']
        
        # Invalid port (not an integer)
        result = validate_smtp_config({
            'name': 'Test SMTP',
            'email_address': 'test@example.com',
            'smtp_host': 'smtp.example.com',
            'smtp_port': 'abc',  # Not an integer
            'username': 'test@example.com',
            'password': 'password123'
        })
        assert result['valid'] is False
        assert 'SMTP port must be an integer' in result['message']
        
        # Invalid daily limit
        result = validate_smtp_config({
            'name': 'Test SMTP',
            'email_address': 'test@example.com',
            'smtp_host': 'smtp.example.com',
            'smtp_port': 587,
            'username': 'test@example.com',
            'password': 'password123',
            'daily_limit': 0  # Too low
        })
        assert result['valid'] is False
        assert 'Daily limit must be at least 1' in result['message']