"""
Unit tests for JWT functions - minimal version.

This module contains only the essential JWT tests.
"""

import pytest
import jwt
from datetime import datetime, timedelta
from auth.server import create_jwt


class TestJWTFunctions:
    """Unit tests for JWT token creation functionality."""

    def test_create_jwt_basic(self):
        """Test basic JWT token creation."""
        username = "test@example.com"
        secret = "test_secret_key"
        is_admin = False
        token = create_jwt(username, secret, is_admin)
        assert isinstance(token, str)
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        assert decoded['username'] == username
        assert decoded['admin'] == is_admin
        assert 'exp' in decoded
        assert 'iat' in decoded
        print("✅ Basic JWT token creation works")

    def test_create_jwt_with_admin(self):
        """Test JWT token creation with admin privileges."""
        username = "admin@example.com"
        secret = "test_secret_key"
        is_admin = True
        token = create_jwt(username, secret, is_admin)
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        assert decoded['admin'] is True
        print("✅ Admin JWT token creation works")

    def test_create_jwt_expiration(self):
        """Test JWT token expiration."""
        username = "test@example.com"
        secret = "test_secret_key"
        is_admin = False
        token = create_jwt(username, secret, is_admin)
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        assert 'exp' in decoded
        assert 'iat' in decoded
        # Check that expiration is in the future
        assert decoded['exp'] > datetime.utcnow().timestamp()
        print("✅ JWT token expiration works") 