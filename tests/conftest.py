import pytest
import os
import tempfile
from peewee import SqliteDatabase
from flask import Flask
import json
import queue
from unittest.mock import MagicMock, patch

from models.email_model import EmailMessage, db as _db
from models.smtp_config import SmtpConfig
from services.email_service import EmailService
from services.queue_service import EmailQueue
from controllers.email_controller import EmailController, email_bp
from controllers.smtp_controller import SmtpController, smtp_bp
from app import create_app

@pytest.fixture(scope='function')
def db():
    """Create a test database in memory"""
    test_db = SqliteDatabase(':memory:')
    
    # Connect to the test database
    with test_db.bind_ctx([EmailMessage, SmtpConfig]):
        test_db.connect()
        test_db.create_tables([EmailMessage, SmtpConfig])
        
        yield test_db
        
        # Clean up
        test_db.drop_tables([EmailMessage, SmtpConfig])
        test_db.close()

@pytest.fixture
def smtp_config(db):
    """Create a test SMTP configuration"""
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
    return config

@pytest.fixture
def mock_queue():
    """Create a mock queue service"""
    mock = MagicMock(spec=EmailQueue)
    mock.enqueue = MagicMock()
    return mock

@pytest.fixture
def email_service(mock_queue):
    """Create an email service with mock queue"""
    service = EmailService(mock_queue)
    return service

@pytest.fixture
def test_email(db, smtp_config):
    """Create a test email in the database"""
    email = EmailMessage.create(
        subject="Test Subject",
        sender="",
        recipients=json.dumps(["recipient@example.com"]),
        html_content="<p>Test content</p>",
        status="queued",
        smtp_config_id=smtp_config.id,
        priority=1
    )
    return email

@pytest.fixture
def app():
    """Create a Flask test app"""
    # Create a temporary file for the test database
    db_fd, db_path = tempfile.mkstemp()
    
    # Configure the app for testing
    app = Flask(__name__)
    app.config['TESTING'] = True
    
    # Create a mock queue service
    mock_queue = MagicMock(spec=EmailQueue)
    
    # Create an email service with mock queue
    email_service = EmailService(mock_queue)
    
    # Setup controllers
    email_controller = EmailController(email_service)
    email_controller.register_routes(email_bp)
    
    smtp_controller = SmtpController(email_service)
    smtp_controller.register_routes(smtp_bp)
    
    # Register blueprints
    app.register_blueprint(email_bp, url_prefix='/api')
    app.register_blueprint(smtp_bp, url_prefix='/api')
    
    # Pass the app to the tests
    with app.app_context():
        yield app
    
    # Clean up
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """Create a test client for the app"""
    return app.test_client()