from flask import Blueprint, request, jsonify
from services.email_service import EmailService
from utils.validators import validate_smtp_config
from models import SmtpConfig
from functools import wraps
import os
smtp_bp = Blueprint('smtp', __name__)
API_KEY = os.getenv('APIKEY')

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        key = request.headers.get('X-API-KEY')
        if key != API_KEY:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function
class SmtpController:
    """Controller for SMTP configuration endpoints"""
    
    def __init__(self, email_service: EmailService):
        self.email_service = email_service
    
    def register_routes(self, blueprint: Blueprint):
        """Register routes to blueprint"""
        blueprint.route('/smtp-configs', methods=['POST'])(require_api_key(self.create_smtp_config))
        blueprint.route('/smtp-configs', methods=['GET'])(require_api_key(self.list_smtp_configs))
        blueprint.route('/smtp-configs/<int:config_id>', methods=['GET'])(require_api_key(self.get_smtp_config))
        blueprint.route('/smtp-configs/<int:config_id>', methods=['PUT'])(require_api_key(self.update_smtp_config))
    
    def create_smtp_config(self):
        """Create a new SMTP configuration"""
        data = request.json
        
        # Validate input
        validation_result = validate_smtp_config(data)
        if not validation_result['valid']:
            return jsonify({'error': validation_result['message']}), 400
        
        try:
            config_id = self.email_service.create_smtp_config(**data)
            
            return jsonify({
                'message': 'SMTP configuration created successfully',
                'config_id': config_id
            }), 201
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def list_smtp_configs(self):
        """List all SMTP configurations"""
        try:
            configs = self.email_service.list_smtp_configs()
            return jsonify(configs), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def get_smtp_config(self, config_id):
        """Get SMTP configuration details"""
        try:
            config = self.email_service.get_smtp_config(config_id)
            return jsonify(config), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 404
    
    def update_smtp_config(self, config_id):
        """Update an SMTP configuration"""
        data = request.json
        configentity=SmtpConfig.get_or_none(SmtpConfig.id==config_id)
        if not configentity or len(dict(data).items())<1:
            return jsonify({"status":"failed","message":"Config does not exists!"}),400
        try:
            success = self.email_service.update_smtp_config(config_id, **data)
            
            if success:
                return jsonify({'message': 'SMTP configuration updated successfully'}), 200
            else:
                return jsonify({'error': 'Failed to update SMTP configuration'}), 500
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500
