import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration"""
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key')
    DEBUG = False
    
    # Queue configuration
    QUEUE_WORKERS = int(os.environ.get('QUEUE_WORKERS', 2))
    MAX_RETRIES = int(os.environ.get('MAX_RETRIES', 3))

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    QUEUE_WORKERS = int(os.environ.get('QUEUE_WORKERS', 4))

# Select configuration based on environment
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'default')
    return config.get(env, config['default'])