import pytest
import json
from unittest.mock import MagicMock, patch

from controllers.smtp_controller import SmtpController

class TestSmtpController:
    def test_create_smtp_config_success(self, client, email_service):
        """Test successfully creating an SMTP config via API"""
        # Mock the create_smtp_config method
        email_service.create_smtp_config = MagicMock(return_value=1)
        
        # Create a test client
        with patch('controllers.smtp_controller.SmtpController.email_service', email_service):
            # Send request
            response = client.post(
                '/api/smtp-configs',
                json={
                    'name': 'Test SMTP',
                    'email_address': 'test@example.com',
                    'smtp_host': 'smtp.example.com',
                    'smtp_port': 587,
                    'username': 'test@example.com',
                    'password': 'password123',
                    'use_tls': True
                }
            )
            
            # Check response
            assert response.status_code == 201
            data = json.loads(response.data)
            assert data['message'] == 'SMTP configuration created successfully'
            assert data['config_id'] == 1
            
            # Verify service was called correctly
            email_service.create_smtp_config.assert_called_once_with(
                name='Test SMTP',
                email_address='test@example.com',
                smtp_host='smtp.example.com',
                smtp_port=587,
                username='test@example.com',
                password='password123',
                use_tls=True
            )
    
    def test_create_smtp_config_validation_error(self, client):
        """Test validation error when creating an SMTP config"""
        # Send request with invalid email
        response = client.post(
            '/api/smtp-configs',
            json={
                'name': 'Test SMTP',
                'email_address': 'invalid-email',  # Invalid email format
                'smtp_host': 'smtp.example.com',
                'smtp_port': 587,
                'username': 'test@example.com',
                'password': 'password123'
            }
        )
        
        # Check response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'email address' in data['error']
    
    def test_list_smtp_configs(self, client, email_service):
        """Test listing SMTP configs"""
        # Mock the list_smtp_configs method
        email_service.list_smtp_configs = MagicMock(return_value=[
            {'id': 1, 'name': 'SMTP 1', 'email_address': 'smtp1@example.com'},
            {'id': 2, 'name': 'SMTP 2', 'email_address': 'smtp2@example.com'}
        ])
        
        # Create a test client
        with patch('controllers.smtp_controller.SmtpController.email_service', email_service):
            # Send request
            response = client.get('/api/smtp-configs')
            
            # Check response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data) == 2
            assert data[0]['id'] == 1
            assert data[1]['name'] == 'SMTP 2'
            
            # Verify service was called
            email_service.list_smtp_configs.assert_called_once()
    
    def test_get_smtp_config(self, client, email_service):
        """Test getting SMTP config details"""
        # Mock the get_smtp_config method
        email_service.get_smtp_config = MagicMock(return_value={
            'id': 1,
            'name': 'Test SMTP',
            'email_address': 'test@example.com',
            'smtp_host': 'smtp.example.com'
        })
        
        # Create a test client
        with patch('controllers.smtp_controller.SmtpController.email_service', email_service):
            # Send request
            response = client.get('/api/smtp-configs/1')
            
            # Check response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['id'] == 1
            assert data['name'] == 'Test SMTP'
            
            # Verify service was called correctly
            email_service.get_smtp_config.assert_called_once_with(1)
    
    def test_update_smtp_config(self, client, email_service):
        """Test updating an SMTP config"""
        # Mock the update_smtp_config method
        email_service.update_smtp_config = MagicMock(return_value=True)
        
        # Create a test client
        with patch('controllers.smtp_controller.SmtpController.email_service', email_service):
            # Send request
            response = client.put(
                '/api/smtp-configs/1',
                json={
                    'active': False,
                    'daily_limit': 200
                }
            )
            
            # Check response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['message'] == 'SMTP configuration updated successfully'
            
            # Verify service was called correctly
            email_service.update_smtp_config.assert_called_once_with(
                1, active=False, daily_limit=200
            )