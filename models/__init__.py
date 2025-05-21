# models/__init__.py

# Import database instance
from models.email_model import db

# Import models
from models.email_model import EmailMessage
from models.smtp_config import SmtpConfig

# Import initialization function
from models.smtp_config import initialize_db

__all__ = [
    'db',
    'EmailMessage',
    'SmtpConfig',
    'initialize_db'
]