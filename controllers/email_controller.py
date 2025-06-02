from flask import Blueprint, request, jsonify
from services.email_service import EmailService
from utils.validators import validate_email_input
from functools import wraps
import os
email_bp = Blueprint('email', __name__)
API_KEY = os.getenv('APIKEY')

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        key = request.headers.get('X-API-KEY')
        if key != API_KEY:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function
class EmailController:
    """Controller for email endpoints"""
    
    def __init__(self, email_service: EmailService):
        self.email_service = email_service
    
    def register_routes(self, blueprint: Blueprint):
        """Register routes to blueprint"""
        blueprint.route('/emails', methods=['POST'])(require_api_key(self.create_email))
        blueprint.route('/emails/<int:email_id>', methods=['GET'])(require_api_key(self.get_email))
        blueprint.route('/emails/status/<status>', methods=['GET'])(require_api_key(self.get_emails_by_status))
    
    def create_email(self):
        """Create a new email"""
        data = request.json
        
        # Validate input
        validation_result = validate_email_input(data)
        if not validation_result['valid']:
            return jsonify({'error': validation_result['message']}), 400
        
        try:
            email_id = self.email_service.create_email(
                subject=data['subject'],
                recipients=data['recipients'],
                html_content=data['html_content'],
                smtp_config_id=data.get('smtp_config_id'),
                cc=data.get('cc'),
                bcc=data.get('bcc'),
                priority=data.get('priority', 1)
            )
            
            return jsonify({
                'message': 'Email created and queued successfully',
                'email_id': email_id
            }), 201
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def get_email(self, email_id):
        """Get email details by ID"""
        try:
            email = self.email_service.get_email(email_id)
            return jsonify(email), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 404
    
    def get_emails_by_status(self, status):
        """Get emails by status"""
        try:
            limit = request.args.get('limit', 100, type=int)
            emails = self.email_service.get_emails_by_status(status, limit)
            return jsonify(emails), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
