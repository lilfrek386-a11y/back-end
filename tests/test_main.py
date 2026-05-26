from fastapi import status
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "status_code": status.HTTP_200_OK,
        "detail": "ok",
        "result": "working"
    }