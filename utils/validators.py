import re
from typing import Dict, Any

def is_valid_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_email_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate email input data"""
    # Check required fields
    required_fields = ['subject', 'recipients', 'html_content']
    for field in required_fields:
        if field not in data:
            return {
                'valid': False,
                'message': f"Missing required field: {field}"
            }
    
    # Validate recipients
    if not isinstance(data['recipients'], list) or len(data['recipients']) == 0:
        return {
            'valid': False,
            'message': "Recipients must be a non-empty list"
        }
    
    for recipient in data['recipients']:
        if not is_valid_email(recipient):
            return {
                'valid': False,
                'message': f"Invalid recipient email format: {recipient}"
            }
    
    # Validate CC if present
    if 'cc' in data and data['cc']:
        if not isinstance(data['cc'], list):
            return {
                'valid': False,
                'message': "CC must be a list"
            }
        
        for cc in data['cc']:
            if not is_valid_email(cc):
                return {
                    'valid': False,
                    'message': f"Invalid CC email format: {cc}"
                }
    
    # Validate BCC if present
    if 'bcc' in data and data['bcc']:
        if not isinstance(data['bcc'], list):
            return {
                'valid': False,
                'message': "BCC must be a list"
            }
        
        for bcc in data['bcc']:
            if not is_valid_email(bcc):
                return {
                    'valid': False,
                    'message': f"Invalid BCC email format: {bcc}"
                }
    
    # Validate priority if present
    if 'priority' in data:
        try:
            priority = int(data['priority'])
            if priority < 1 or priority > 5:
                return {
                    'valid': False,
                    'message': "Priority must be between 1 and 5"
                }
        except (ValueError, TypeError):
            return {
                'valid': False,
                'message': "Priority must be an integer"
            }
    
    return {
        'valid': True
    }

def validate_smtp_config(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate SMTP configuration input data"""
    # Check required fields
    required_fields = ['name', 'email_address', 'smtp_host', 'smtp_port', 'username', 'password']
    for field in required_fields:
        if field not in data:
            return {
                'valid': False,
                'message': f"Missing required field: {field}"
            }
    
    # Validate email address
    if not is_valid_email(data['email_address']):
        return {
            'valid': False,
            'message': "Invalid email address format"
        }
    
    # Validate port
    try:
        port = int(data['smtp_port'])
        if port < 1 or port > 65535:
            return {
                'valid': False,
                'message': "SMTP port must be between 1 and 65535"
            }
    except (ValueError, TypeError):
        return {
            'valid': False,
            'message': "SMTP port must be an integer"
        }
    
    # Validate limits if present
    if 'daily_limit' in data:
        try:
            daily_limit = int(data['daily_limit'])
            if daily_limit < 1:
                return {
                    'valid': False,
                    'message': "Daily limit must be at least 1"
                }
        except (ValueError, TypeError):
            return {
                'valid': False,
                'message': "Daily limit must be an integer"
            }
    
    if 'hourly_limit' in data:
        try:
            hourly_limit = int(data['hourly_limit'])
            if hourly_limit < 1:
                return {
                    'valid': False,
                    'message': "Hourly limit must be at least 1"
                }
        except (ValueError, TypeError):
            return {
                'valid': False,
                'message': "Hourly limit must be an integer"
            }
    
    return {
        'valid': True
    }