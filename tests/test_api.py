"""Tests for KidsColorAI API routes"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200


def test_generate_coloring_book(client):
    response = client.post("/api/generate", json={
        "theme": "Dinosaurs",
        "page_count": 5,
        "image_size": 512
    })
    assert response.status_code == 200
    data = response.json()
    assert data["theme"] == "Dinosaurs"
    assert data["page_count"] == 5
    assert data["status"] == "PENDING"


def test_get_job_status_not_found(client):
    response = client.get("/api/job/99999")
    assert response.status_code == 404


def test_get_pages_not_found(client):
    response = client.get("/api/pages/99999")
    assert response.status_code == 404


def test_get_pdf_not_completed(client):
    response = client.post("/api/generate", json={
        "theme": "Test",
        "page_count": 1
    })
    job_id = response.json()["id"]
    pdf_response = client.get(f"/api/pdf/{job_id}")
    assert pdf_response.status_code == 400