"""
Security tests - minimal version.

This module contains only the essential security tests.
"""

import pytest
import time
import jwt
from auth.server import hash_password, verify_password, create_jwt


class TestSecurity:
    """Security tests for authentication functions."""

    def test_password_verification_timing(self):
        """Test that password verification has consistent timing to prevent timing attacks."""
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        # Test correct password timing
        start_time = time.time()
        verify_password(password, hashed)
        correct_time = time.time() - start_time
        
        # Test incorrect password timing
        start_time = time.time()
        verify_password("WrongPassword123!", hashed)
        incorrect_time = time.time() - start_time
        
        # Timing should be similar (within 10ms)
        time_diff = abs(correct_time - incorrect_time)
        assert time_diff < 0.01, f"Timing difference too large: {time_diff:.4f}s"
        print("✅ Password verification timing is secure")

    def test_jwt_token_security(self):
        """Test JWT token security characteristics."""
        username = "test@example.com"
        secret = "test_secret_key"
        is_admin = False
        
        # Create token
        token = create_jwt(username, secret, is_admin)
        
        # Test token structure
        assert isinstance(token, str)
        assert len(token) > 50  # Should be reasonably long
        
        # Test token can be decoded with correct secret
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        assert decoded['username'] == username
        assert decoded['admin'] == is_admin
        
        # Test token cannot be decoded with wrong secret
        try:
            jwt.decode(token, "wrong_secret", algorithms=["HS256"])
            pytest.fail("Token should not decode with wrong secret")
        except jwt.InvalidSignatureError:
            pass  # Expected
        
        print("✅ JWT token security is correct") 