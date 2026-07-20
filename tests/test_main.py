from fastapi.testclient import TestClient

from app.main import app
from core.services.portfolio_service import SearchRequest

client = TestClient(app)


def test_homepage():

    response = client.get("/")

    assert response.status_code == 200


def test_invalid_portfolio_category():

    response = client.get(
        "api/portfolio/grants",
        params={
            "year": 2025,
            "category": "not_a_category",
        },
    )

    assert response.status_code == 400

    assert "Invalid category" in response.json()["detail"]
