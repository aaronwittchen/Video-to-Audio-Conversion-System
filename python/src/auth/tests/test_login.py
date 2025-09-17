import base64


def test_login_success(client):
    """Test successful login after registration."""
    # First register a user
    client.post("/register", json={
        "email": "login@example.com",
        "password": "StrongPass1!"
    })
    
    # Create basic auth header
    credentials = base64.b64encode(b"login@example.com:StrongPass1!").decode('utf-8')
    headers = {"Authorization": f"Basic {credentials}"}
    
    response = client.post("/login", headers=headers)
    data = response.get_json()
    
    assert response.status_code == 200
    assert data["status"] == "success"
    assert "data" in data
    assert "token" in data["data"]
    assert data["data"]["token"].startswith("eyJ")  # JWT tokens start with eyJ


def test_login_invalid_password(client):
    """Test login with wrong password."""
    # Register a user
    client.post("/register", json={
        "email": "login@example.com",
        "password": "StrongPass1!"
    })
    
    # Try to login with wrong password
    credentials = base64.b64encode(b"login@example.com:WrongPassword").decode('utf-8')
    headers = {"Authorization": f"Basic {credentials}"}
    
    response = client.post("/login", headers=headers)
    data = response.get_json()
    
    assert response.status_code == 401
    assert data["status"] == "error"
    assert data["message"] == "Could not verify"


def test_login_nonexistent_user(client):
    """Test login with user that doesn't exist."""
    credentials = base64.b64encode(b"nonexistent@example.com:Password123!").decode('utf-8')
    headers = {"Authorization": f"Basic {credentials}"}
    
    response = client.post("/login", headers=headers)
    data = response.get_json()
    
    assert response.status_code == 401
    assert data["status"] == "error"
    assert data["message"] == "Could not verify"


def test_login_missing_auth_header(client):
    """Test login without authorization header."""
    response = client.post("/login")
    data = response.get_json()
    
    assert response.status_code == 401
    assert data["status"] == "error"
    assert data["message"] == "Could not verify"