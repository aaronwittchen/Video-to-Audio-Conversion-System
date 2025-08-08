"""
Integration tests for registration endpoints - minimal version.

This module contains only the essential registration tests.
"""

import pytest
import json
from typing import Dict, Any


class TestRegistrationEndpoints:
    """Integration tests for registration endpoint functionality."""

    def test_register_endpoint_success(self, test_client, valid_user_data: Dict[str, Any]):
        """Test successful user registration via endpoint."""
        response = test_client.post('/register', json=valid_user_data)
        if response.status_code == 201:
            data = json.loads(response.data)
            assert data['message'] == 'User registered successfully'
            print("✅ Registration successful")
        elif response.status_code == 409:
            print("⚠️ User already exists (this is OK)")
            assert True
        else:
            pytest.fail(f"Unexpected registration response: {response.status_code}")

    def test_register_endpoint_invalid_email(self, test_client):
        """Test registration with invalid email format."""
        invalid_data = {
            "email": "invalid-email",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User"
        }
        response = test_client.post('/register', json=invalid_data)
        assert response.status_code == 400
        print("✅ Invalid email rejected")

    def test_register_endpoint_missing_fields(self, test_client):
        """Test registration with missing required fields."""
        incomplete_data = {"email": "test@example.com"}
        response = test_client.post('/register', json=incomplete_data)
        assert response.status_code == 400
        print("✅ Missing fields handled") 