import unittest
from server import hash_password, verify_password, validate_password_strength

class TestPasswordUtils(unittest.TestCase):
    def test_password_hashing(self):
        """Test that password hashing and verification works correctly."""
        password = "mypassword"

        hashed = hash_password(password)
        
        self.assertNotEqual(password, hashed, "Hashed password should not match plain text")
        
        self.assertTrue(verify_password(password, hashed), "Correct password should verify successfully")
        
        self.assertFalse(verify_password("wrongpassword", hashed), "Wrong password should fail verification")
    
    def test_password_strength(self):
        """Test password strength validation."""
        weak_password = "Weak1"
        result = validate_password_strength(weak_password)
        self.assertIsNotNone(result, f"Weak password '{weak_password}' should fail validation")
        
        strong_password = "StrongPass1!"
        result = validate_password_strength(strong_password)
        self.assertIsNone(result, f"Strong password '{strong_password}' should pass validation")

if __name__ == '__main__':
    unittest.main()
