"""
Tests for Flask application endpoints
"""

import pytest
from unittest.mock import patch, Mock
from src.main import app


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestAPIEndpoints:
    """Tests for API endpoints"""
    
    def test_index_route(self, client):
        """Test the index route serves HTML"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'<!DOCTYPE html>' in response.data
    
    @patch('src.api.routes.check_adb_available')
    def test_check_adb_success(self, mock_check, client):
        """Test /api/check-adb endpoint when ADB is available"""
        mock_check.return_value = (True, "ADB version 1.0.41")
        
        response = client.get('/api/check-adb')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['available'] is True
        assert 'timestamp' in data
    
    @patch('src.api.routes.check_adb_available')
    def test_check_adb_not_found(self, mock_check, client):
        """Test /api/check-adb endpoint when ADB is not found"""
        mock_check.return_value = (False, "ADB not found in PATH")
        
        response = client.get('/api/check-adb')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['available'] is False
    
    @patch('src.api.routes.get_connected_devices')
    def test_get_devices(self, mock_devices, client):
        """Test /api/devices endpoint"""
        mock_devices.return_value = [
            {'id': 'device1', 'model': 'Pixel 6', 'status': 'connected'},
            {'id': 'device2', 'model': 'Galaxy S21', 'status': 'connected'}
        ]
        
        response = client.get('/api/devices')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        assert len(data['data']['devices']) == 2
    
    @patch('src.api.routes.get_categories_json')
    def test_get_categories(self, mock_categories, client):
        """Test /api/categories endpoint"""
        mock_categories.return_value = [
            {
                'id': 'test_category',
                'name': 'Test Category',
                'impact': 'high',
                'commands': []
            }
        ]
        
        response = client.get('/api/categories')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        assert len(data['data']['categories']) == 1
    
    @patch('src.api.routes.execute_adb_command')
    def test_execute_command_success(self, mock_execute, client):
        """Test /api/execute endpoint with successful command"""
        mock_execute.return_value = (True, "Command executed", "")
        
        response = client.post('/api/execute', json={
            'device_id': 'device123',
            'command': 'shell settings put global test 1',
            'action': 'enable'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'output' in data['data']
    
    def test_execute_command_missing_device(self, client):
        """Test /api/execute endpoint without device_id"""
        response = client.post('/api/execute', json={
            'command': 'shell settings put global test 1'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'device' in data['error'].lower()
    
    def test_execute_command_missing_command(self, client):
        """Test /api/execute endpoint without command"""
        response = client.post('/api/execute', json={
            'device_id': 'device123'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'command' in data['error'].lower()
    
    @patch('src.api.routes.execute_adb_command')
    def test_execute_command_failure(self, mock_execute, client):
        """Test /api/execute endpoint with failed command"""
        mock_execute.return_value = (False, "", "error: device not found")
        
        response = client.post('/api/execute', json={
            'device_id': 'invalid_device',
            'command': 'shell settings put global test 1',
            'action': 'enable'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False


class TestAPIResponseFormat:
    """Tests for standardized API response format"""
    
    @patch('src.api.routes.get_connected_devices')
    def test_response_has_success_field(self, mock_devices, client):
        """Test all responses have 'success' field"""
        mock_devices.return_value = []
        
        response = client.get('/api/devices')
        data = response.get_json()
        
        assert 'success' in data
        assert isinstance(data['success'], bool)
    
    @patch('src.api.routes.get_connected_devices')
    def test_response_has_timestamp(self, mock_devices, client):
        """Test all responses have 'timestamp' field"""
        mock_devices.return_value = []
        
        response = client.get('/api/devices')
        data = response.get_json()
        
        assert 'timestamp' in data
        assert isinstance(data['timestamp'], str)
    
    @patch('src.api.routes.get_connected_devices')
    def test_success_response_has_data(self, mock_devices, client):
        """Test successful responses have 'data' field"""
        mock_devices.return_value = []
        
        response = client.get('/api/devices')
        data = response.get_json()
        
        assert data['success'] is True
        assert 'data' in data
    
    def test_error_response_has_error_field(self, client):
        """Test error responses have 'error' field"""
        response = client.post('/api/execute', json={})
        data = response.get_json()
        
        assert data['success'] is False
        assert 'error' in data
        assert isinstance(data['error'], str)

