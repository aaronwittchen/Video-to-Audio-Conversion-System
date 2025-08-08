"""
Integration tests for login endpoints - minimal version.

This module contains only the essential login tests.
"""

import pytest
import json
from typing import Dict, Any


class TestLoginEndpoints:
    """Integration tests for login endpoint functionality."""

    def test_login_endpoint_success(self, test_client, valid_user_data: Dict[str, Any], auth_headers: Dict[str, str]):
        """Test successful login via endpoint."""
        # Ensure user exists
        test_client.post('/register', json=valid_user_data)
        
        # Login
        response = test_client.post('/login', headers=auth_headers)
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'token' in data
            assert 'user' in data
            print("✅ Login successful")
        else:
            pytest.fail(f"Login failed: {response.status_code}")

    def test_login_endpoint_invalid_credentials(self, test_client, valid_user_data: Dict[str, Any]):
        """Test login with invalid credentials."""
        # Ensure user exists
        test_client.post('/register', json=valid_user_data)
        
        # Try to login with wrong password
        import base64
        wrong_credentials = base64.b64encode(b"test@example.com:wrongpassword").decode('utf-8')
        headers = {'Authorization': f'Basic {wrong_credentials}'}
        
        response = test_client.post('/login', headers=headers)
        assert response.status_code == 401
        print("✅ Invalid credentials rejected") 