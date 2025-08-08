import pytest
import os
import base64
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from auth.server import server

# Load test environment variables
load_dotenv('.env.test')

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Set up test environment variables for the entire test session.
    
    This fixture runs once per test session and configures:
    - JWT secret for testing
    - Database connection parameters
    - Test-specific configurations
    """
    # Ensure JWT_SECRET is set for testing
    os.environ['JWT_SECRET'] = 'test_jwt_secret_key_for_testing'
    yield

@pytest.fixture
def test_config():
    """
    Provide test-specific configuration.
    
    Returns:
        Dict containing test configuration including database URLs,
        JWT settings, and feature flags for testing.
    """
    return {
        "database_url": os.environ.get('TEST_DATABASE_URL', 'mysql://auth_user:auth_password@localhost:3306/test_auth_db'),
        "jwt_secret": "test_jwt_secret_key_for_testing",
        "email_enabled": False,  # Disable real emails in tests
        "rate_limit_enabled": False,  # Disable rate limiting in tests
        "mysql_host": os.environ.get('TEST_MYSQL_HOST', 'localhost'),
        "mysql_user": os.environ.get('TEST_MYSQL_USER', 'auth_user'),
        "mysql_password": os.environ.get('TEST_MYSQL_PASSWORD', 'auth_password'),
        "mysql_db": os.environ.get('TEST_MYSQL_DB', 'test_auth_db'),
        "mysql_port": int(os.environ.get('TEST_MYSQL_PORT', 3306))
    }

@pytest.fixture
def test_client(test_config):
    """
    Create Flask test client with test database configuration.
    
    Args:
        test_config: Test configuration fixture
        
    Returns:
        Flask test client configured for testing
    """
    # Configure Flask app for testing
    server.config['TESTING'] = True
    server.config['MYSQL_HOST'] = test_config['mysql_host']
    server.config['MYSQL_USER'] = test_config['mysql_user']
    server.config['MYSQL_PASSWORD'] = test_config['mysql_password']
    server.config['MYSQL_DB'] = test_config['mysql_db']
    server.config['MYSQL_PORT'] = test_config['mysql_port']
    
    # Create a custom test client that handles MySQL connections properly
    class CustomTestClient:
        def __init__(self, app):
            self.app = app
            self.client = app.test_client()
        
        def __getattr__(self, name):
            return getattr(self.client, name)
        
        def __enter__(self):
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            # Don't let Flask-MySQLdb handle teardown automatically
            pass
    
    with CustomTestClient(server) as client:
        yield client

# Test Data Management Fixtures
@pytest.fixture
def valid_user_data() -> Dict[str, Any]:
    """
    Provide valid user data for registration tests.
    
    Returns:
        Dict containing valid user registration data
    """
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "first_name": "Test",
        "last_name": "User"
    }

@pytest.fixture
def existing_user_data() -> Dict[str, Any]:
    """
    Provide data for a user that already exists in the database.
    
    Returns:
        Dict containing data for an existing user
    """
    return {
        "email": "existing@example.com", 
        "password": "ExistingPass123!",
        "first_name": "Existing",
        "last_name": "User"
    }

@pytest.fixture
def invalid_user_data() -> Dict[str, Any]:
    """
    Provide invalid user data for validation tests.
    
    Returns:
        Dict containing invalid user registration data
    """
    return {
        "email": "invalid-email",
        "password": "weak",
        "first_name": "",
        "last_name": ""
    }

@pytest.fixture
def edge_case_user_data() -> Dict[str, Any]:
    """
    Provide edge case user data for boundary testing.
    
    Returns:
        Dict containing edge case user data
    """
    return {
        "email": "very.long.email.address.with.many.dots@very.long.domain.example.com",
        "password": "A" * 128,  # Very long password
        "first_name": "A" * 50,  # Very long first name
        "last_name": "B" * 50    # Very long last name
    }

@pytest.fixture
def sample_user() -> Dict[str, Any]:
    """
    Legacy fixture for backward compatibility.
    
    Returns:
        Dict containing basic user data
    """
    return {
        'email': 'test@example.com',
        'password': 'testpassword123'
    }

@pytest.fixture
def auth_headers(valid_user_data) -> Dict[str, str]:
    """
    Create authentication headers for login tests.
    
    Args:
        valid_user_data: Valid user data fixture
        
    Returns:
        Dict containing Basic Auth headers
    """
    email = valid_user_data['email']
    password = valid_user_data['password']
    credentials = base64.b64encode(f'{email}:{password}'.encode()).decode('utf-8')
    return {'Authorization': f'Basic {credentials}'}

@pytest.fixture
def wrong_password_headers(valid_user_data) -> Dict[str, str]:
    """
    Create authentication headers with wrong password.
    
    Args:
        valid_user_data: Valid user data fixture
        
    Returns:
        Dict containing Basic Auth headers with wrong password
    """
    email = valid_user_data['email']
    wrong_password = 'wrongpassword'
    credentials = base64.b64encode(f'{email}:{wrong_password}'.encode()).decode('utf-8')
    return {'Authorization': f'Basic {credentials}'}

@pytest.fixture
def valid_token(test_client, valid_user_data, auth_headers) -> Optional[str]:
    """
    Get a valid JWT token for authenticated tests.
    
    Args:
        test_client: Flask test client
        valid_user_data: Valid user data fixture
        auth_headers: Authentication headers fixture
        
    Returns:
        Valid JWT token string or None if login fails
    """
    import json
    
    # Ensure user exists
    test_client.post('/register', json=valid_user_data)
    
    # Login to get token
    response = test_client.post('/login', headers=auth_headers)
    
    if response.status_code == 200:
        data = json.loads(response.data)
        return data.get('token')
    return None

# Database Management Utilities
def cleanup_test_database():
    """
    Utility function to manually clean test database.
    
    This function removes all test data from the database
    to ensure a clean state for testing.
    """
    import mysql.connector
    
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('TEST_MYSQL_HOST', 'localhost'),
            user=os.environ.get('TEST_MYSQL_USER', 'auth_user'),
            password=os.environ.get('TEST_MYSQL_PASSWORD', 'auth_password'),
            database=os.environ.get('TEST_MYSQL_DB', 'test_auth_db')
        )
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users")
        conn.commit()
        print("✅ Test database cleaned")
        
    except Exception as e:
        print(f"⚠️ Database cleanup failed: {e}")
    finally:
        if 'conn' in locals():
            cursor.close()
            conn.close()

def show_database_state():
    """
    Display current state of test database.
    
    This function shows all users in the test database
    for debugging purposes.
    """
    import mysql.connector
    
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('TEST_MYSQL_HOST', 'localhost'),
            user=os.environ.get('TEST_MYSQL_USER', 'auth_user'),
            password=os.environ.get('TEST_MYSQL_PASSWORD', 'auth_password'),
            database=os.environ.get('TEST_MYSQL_DB', 'test_auth_db')
        )
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, email, created_at FROM users")
        users = cursor.fetchall()
        
        print(f"\n📊 Test Database State:")
        print(f"Total users: {len(users)}")
        for user in users:
            print(f"  - ID: {user[0]}, Email: {user[1]}, Created: {user[2]}")
        
    except Exception as e:
        print(f"❌ Failed to check database state: {e}")
    finally:
        if 'conn' in locals():
            cursor.close()
            conn.close()

# Manual cleanup if needed
if __name__ == "__main__":
    print("Manual database cleanup...")
    show_database_state()
    cleanup_test_database()