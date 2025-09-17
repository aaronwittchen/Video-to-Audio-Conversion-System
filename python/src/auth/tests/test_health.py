def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    data = response.get_json()

    assert response.status_code == 200
    assert data["status"] == "success"
    assert data["data"]["status"] == "healthy"
