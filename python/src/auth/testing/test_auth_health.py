"""
Health tests - minimal version.

This module contains only the essential health test.
"""

import pytest
import json


class TestHealthCheck:
    """Minimal test suite for health check functionality."""

    def test_health_endpoint(self, test_client):
        """Test health check endpoint."""
        response = test_client.get('/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'status' in data
        assert data['status'] == 'healthy'
        print("✅ Health endpoint works") 