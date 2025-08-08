"""
Unit tests for password functions - minimal version.

This module contains only the essential password tests.
"""

import pytest
import bcrypt
from auth.server import hash_password, verify_password


class TestPasswordFunctions:
    """Unit tests for password hashing functionality."""

    def test_hash_password_basic(self):
        """Test basic password hashing functionality."""
        password = "TestPassword123!"
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert hashed != password
        assert hashed.startswith('$2b$') or hashed.startswith('$2a$')
        print("✅ Basic password hashing works")

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "TestPassword123!"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
        print("✅ Password verification works") 