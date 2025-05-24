import pytest,os,sys

from flask import Flask, Blueprint
from unittest.mock import MagicMock
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from controllers.smtp_controller import SmtpController

@pytest.fixture
def mock_email_service():
    """Create a mock email service for testing"""
    service = MagicMock()
    return service

@pytest.fixture
def smtp_controller(mock_email_service):
    """Create an SMTP controller with a mock email service"""
    return SmtpController(mock_email_service)

@pytest.fixture
def blueprint():
    """Create a fresh blueprint for each test"""
    return Blueprint('smtp', __name__)

@pytest.fixture
def app(blueprint, smtp_controller):
    """Create a Flask test app with the SMTP controller registered"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['DEBUG'] = True
    
    # Register routes to the blueprint
    smtp_controller.register_routes(blueprint)
    
    # Register the blueprint to the app without a prefix
    # This matches your test URLs that don't have a prefix
    app.register_blueprint(blueprint)
    
    return app

@pytest.fixture
def client(app):
    """Create a test client for the app"""
    with app.test_client() as client:
        yield client
        
class TestSmtpController:
	def test_create_smtp_config_success(self, client, mock_email_service):
		mock_email_service.create_smtp_config.return_value = 1
		response = client.post('/smtp-configs', json={
			'smtp_server': 'smtp.example.com',
			'port': 587,
			'username': 'user@example.com',
			'password': 'securepassword'
		})
		assert response.status_code == 201
		assert response.json == {
			'message': 'SMTP configuration created successfully',
			'config_id': 1
		} 


class TestSmtpController:
	def test_list_smtp_configs(self, client, mock_email_service):
		mock_email_service.list_smtp_configs.return_value = [{'id': 1, 'name': 'Test Config'}]
		response = client.get('/smtp-configs')
		assert response.status_code == 200
		assert response.json == [{'id': 1, 'name': 'Test Config'}] 


class TestGetSmtpConfig:
	def test_get_smtp_config_success(self, client, mock_email_service):
		mock_email_service.get_smtp_config.return_value = {'id': 1, 'host': 'smtp.example.com', 'port': 587}
		response = client.get('/smtp-configs/1')
		assert response.status_code == 200
		assert response.json == {'id': 1, 'host': 'smtp.example.com', 'port': 587} 


class TestUpdateSmtpConfig:
	def test_update_smtp_config_success(self, client, mock_email_service):
		mock_email_service.update_smtp_config.return_value = True
		response = client.put('/smtp-configs/1', json={'host': 'smtp.example.com', 'port': 587})
		assert response.status_code == 200
		assert response.get_json() == {'message': 'SMTP configuration updated successfully'} 




class TestGetSmtpConfig:
	def test_get_non_existing_smtp_config(self, client, mock_email_service):
		mock_email_service.get_smtp_config.side_effect = Exception('Not Found')
		response = client.get('/smtp-configs/999')
		assert response.status_code == 404
		assert response.json == {'error': 'Not Found'} 


class TestListSmtpConfigs:
	def test_list_empty_smtp_configs(self, client, mock_email_service):
		mock_email_service.list_smtp_configs.return_value = []
		response = client.get('/smtp-configs')
		assert response.status_code == 200
		assert response.json == []
  
class TestSmtpController:
	def test_update_smtp_config_empty_payload(self, client):
		response = client.put('/smtp-configs/1', json={})
		assert response.status_code == 400
		#assert 'error' in response.get_json()