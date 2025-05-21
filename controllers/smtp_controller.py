from flask import Blueprint, request, jsonify
from services.email_service import EmailService
from utils.validators import validate_smtp_config

smtp_bp = Blueprint('smtp', __name__)

class SmtpController:
    """Controller for SMTP configuration endpoints"""
    
    def __init__(self, email_service: EmailService):
        self.email_service = email_service
    
    def register_routes(self, blueprint: Blueprint):
        """Register routes to blueprint"""
        blueprint.route('/smtp-configs', methods=['POST'])(self.create_smtp_config)
        blueprint.route('/smtp-configs', methods=['GET'])(self.list_smtp_configs)
        blueprint.route('/smtp-configs/<int:config_id>', methods=['GET'])(self.get_smtp_config)
        blueprint.route('/smtp-configs/<int:config_id>', methods=['PUT'])(self.update_smtp_config)
    
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
        
        try:
            success = self.email_service.update_smtp_config(config_id, **data)
            
            if success:
                return jsonify({'message': 'SMTP configuration updated successfully'}), 200
            else:
                return jsonify({'error': 'Failed to update SMTP configuration'}), 500
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500