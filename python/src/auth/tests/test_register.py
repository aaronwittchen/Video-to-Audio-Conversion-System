def test_register_success(client):
    """Test successful user registration."""
    response = client.post("/register", json={
        "email": "user1@example.com",
        "password": "StrongPass1!"
    })
    data = response.get_json()
    assert response.status_code == 201
    assert data["status"] == "success"
    assert data["message"] == "User registered successfully"


def test_register_duplicate(client):
    """Test registration with duplicate email."""
    client.post("/register", json={
        "email": "dup@example.com",
        "password": "StrongPass1!"
    })
    response = client.post("/register", json={
        "email": "dup@example.com",
        "password": "StrongPass1!"
    })
    data = response.get_json()
    assert response.status_code == 409
    assert data["status"] == "error"
    assert data["message"] == "User already exists"


def test_register_missing_fields(client):
    """Test registration with missing email or password."""
    response = client.post("/register", json={
        "email": "user@example.com"
        # missing password
    })
    data = response.get_json()
    assert response.status_code == 400
    assert data["status"] == "error"
    assert data["message"] == "Email and password are required"


def test_register_weak_password(client):
    """Test registration with weak password."""
    response = client.post("/register", json={
        "email": "user@example.com",
        "password": "weak"
    })
    data = response.get_json()
    assert response.status_code == 400
    assert data["status"] == "error"
    assert "Password must contain" in data["message"]