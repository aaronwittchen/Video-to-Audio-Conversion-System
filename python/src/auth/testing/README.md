# Auth Service Testing

Minimal test suite for the Authentication Service with only essential tests.

## 🎯 **Test Categories**

### **Register Flow**
- `test_register_endpoint_success` - Tests successful user registration
- `test_register_endpoint_invalid_email` - Tests invalid email validation
- `test_register_endpoint_missing_fields` - Tests missing required fields

### **Login Flow**
- `test_login_endpoint_success` - Tests successful login
- `test_login_endpoint_invalid_credentials` - Tests invalid credentials

### **Password Functions**
- `test_hash_password_basic` - Tests password hashing
- `test_verify_password_correct` - Tests password verification

### **JWT Functions**
- `test_create_jwt_basic` - Tests basic JWT creation
- `test_create_jwt_with_admin` - Tests admin JWT creation
- `test_create_jwt_expiration` - Tests JWT expiration

### **Security**
- `test_password_verification_timing` - Tests timing attack prevention
- `test_jwt_token_security` - Tests JWT security characteristics

### **Health Check**
- `test_health_endpoint` - Tests health endpoint functionality

## 📁 **Simplified Folder Structure**

```
testing/
├── unit/                    # Unit tests for core functions
│   ├── test_password_functions.py
│   ├── test_jwt_functions.py
│   └── test_security.py
├── integration/             # Integration tests for endpoints
│   ├── test_registration_endpoints.py
│   └── test_login_endpoints.py
├── fixtures/               # Test configuration
│   └── conftest.py
├── config/                 # Pytest configuration
│   └── pytest.ini
├── data/                   # Database setup
│   ├── test_init.sql
│   └── setup_test_db.py
├── test_auth_health.py     # Health check test
└── run_tests.py           # Simple test runner
```

## 🚀 **Running Tests**

### **Single Command Options**

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run using the test runner script
python run_tests.py

# Run with coverage
python run_tests.py --coverage
```

### **Run Specific Test Categories**

```bash
# Run only unit tests
pytest unit/

# Run only integration tests
pytest integration/

# Run only password tests
pytest -m password

# Run only JWT tests
pytest -m jwt

# Run only registration tests
pytest -m registration

# Run only login tests
pytest -m login

# Run only security tests
pytest -m security

# Run only health tests
pytest -m health
```

## 🎯 **Test Coverage**

This minimal test suite covers:

- ✅ **Core Functions**: Password hashing, JWT creation
- ✅ **Endpoints**: Registration, login, health check
- ✅ **Security**: Timing attacks, JWT security
- ✅ **Validation**: Email format, required fields
- ✅ **Error Handling**: Invalid credentials, missing data

## 📊 **Test Data Management**

Tests use fixtures from `conftest.py`:
- `valid_user_data` - Standard test user data
- `test_client` - Flask test client
- `auth_headers` - Authentication headers
- Database setup and cleanup

## 🔧 **Configuration**

- **Database**: Test MySQL database
- **JWT Secret**: Test-specific secret key
- **Environment**: Isolated test environment
- **Timeout**: 30 seconds per test

## ✅ **Benefits**

- **Fast Execution**: Only essential tests
- **Clear Focus**: Each test has a specific purpose
- **Easy Maintenance**: Minimal test code
- **Quick Feedback**: Fast test results
- **Comprehensive**: Covers all critical functionality

## 🎯 **Test Goals**

- **Essential Coverage**: Core authentication functionality
- **Fast Execution**: Complete test suite in <30 seconds
- **Clear Results**: Easy to understand test output
- **Reliable**: Consistent test behavior
- **Maintainable**: Simple test structure 