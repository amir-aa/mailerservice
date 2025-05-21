import pytest
import json
from unittest.mock import MagicMock, patch

from controllers.email_controller import EmailController

class TestEmailController:
    def test_create_email_success(self, client, email_service):
        """Test successfully creating an email via API"""
        # Mock the create_email method
        email_service.create_email = MagicMock(return_value=123)
        
        # Create a test client
        with patch('controllers.email_controller.EmailController.email_service', email_service):
            # Send request
            response = client.post(
                '/api/emails',
                json={
                    'subject': 'Test Subject',
                    'recipients': ['test@example.com'],
                    'html_content': '<p>Test content</p>',
                    'priority': 2
                }
            )
            
            # Check response
            assert response.status_code == 201
            data = json.loads(response.data)
            assert data['message'] == 'Email created and queued successfully'
            assert data['email_id'] == 123
            
            # Verify service was called correctly
            email_service.create_email.assert_called_once_with(
                subject='Test Subject',
                recipients=['test@example.com'],
                html_content='<p>Test content</p>',
                smtp_config_id=None,
                cc=None,
                bcc=None,
                priority=2
            )
    
    def test_create_email_validation_error(self, client):
        """Test validation error when creating an email"""
        # Send request with missing required field
        response = client.post(
            '/api/emails',
            json={
                'subject': 'Test Subject',
                # Missing recipients
                'html_content': '<p>Test content</p>'
            }
        )
        
        # Check response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'recipients' in data['error']
    
    def test_get_email(self, client, email_service):
        """Test getting email details"""
        # Mock the get_email method
        email_service.get_email = MagicMock(return_value={
            'id': 123,
            'subject': 'Test Subject',
            'status': 'sent'
        })
        
        # Create a test client
        with patch('controllers.email_controller.EmailController.email_service', email_service):
            # Send request
            response = client.get('/api/emails/123')
            
            # Check response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['id'] == 123
            assert data['subject'] == 'Test Subject'
            
            # Verify service was called correctly
            email_service.get_email.assert_called_once_with(123)
    
    def test_get_email_not_found(self, client, email_service):
        """Test getting a non-existent email"""
        # Mock the get_email method to raise an exception
        email_service.get_email = MagicMock(side_effect=Exception("Email not found"))
        
        # Create a test client
        with patch('controllers.email_controller.EmailController.email_service', email_service):
            # Send request
            response = client.get('/api/emails/999')
            
            # Check response
            assert response.status_code == 404
            data = json.loads(response.data)
            assert 'error' in data
    
    def test_get_emails_by_status(self, client, email_service):
        """Test getting emails by status"""
        # Mock the get_emails_by_status method
        email_service.get_emails_by_status = MagicMock(return_value=[
            {'id': 1, 'subject': 'Email 1', 'status': 'queued'},
            {'id': 2, 'subject': 'Email 2', 'status': 'queued'}
        ])
        
        # Create a test client
        with patch('controllers.email_controller.EmailController.email_service', email_service):
            # Send request
            response = client.get('/api/emails/status/queued?limit=10')
            
            # Check response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data) == 2
            assert data[0]['id'] == 1
            assert data[1]['subject'] == 'Email 2'
            
            # Verify service was called correctly
            email_service.get_emails_by_status.assert_called_once_with('queued', 10)