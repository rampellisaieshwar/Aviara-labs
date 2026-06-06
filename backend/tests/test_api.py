import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.enrichment import EnrichmentService
from app.services.groq_llm import GroqClassificationService

client = TestClient(app)

def test_health_endpoint():
    """Verify that the health check endpoint returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data
    assert "environment" in data

def test_enrich_endpoint_valid_corporate():
    """Verify enrichment for standard corporate email addresses."""
    payload = {
        "name": "Jane Doe",
        "email": "jane@google.com",
        "company": "Google"
    }
    response = client.post("/enrich", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "linkedin_url" in data
    assert "company_size" in data
    assert "industry" in data
    assert "google" in data["linkedin_url"]
    assert data["company_size"] == "10,000+"
    assert "Technology" in data["industry"]

def test_enrich_endpoint_valid_personal():
    """Verify enrichment details for personal emails."""
    payload = {
        "name": "Bob Smith",
        "email": "bob@gmail.com"
    }
    response = client.post("/enrich", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "linkedin_url" in data
    assert data["company_size"] == "Individual / Freelancer"
    assert data["industry"] == "Consumer"

def test_enrich_endpoint_invalid_email():
    """Verify that malformed email inputs throw Pydantic validation errors (422)."""
    payload = {
        "name": "Jane Doe",
        "email": "not_an_email_address",
        "company": "Acme"
    }
    response = client.post("/enrich", json=payload)
    assert response.status_code == 422  # Unprocessable Entity (validation error)

def test_classify_endpoint_sales():
    """Verify intent classification for sales enquiries using fallback parser."""
    payload = {
        "message": "We would like to get a quote and schedule a product demo for 50 users."
    }
    response = client.post("/classify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "sales_enquiry"
    assert data["confidence"] > 0.7

def test_classify_endpoint_spam():
    """Verify classification of spam inputs."""
    payload = {
        "message": "Buy cheap bitcoin now and get 500% returns, guaranteed wealth!"
    }
    response = client.post("/classify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "spam"
    assert data["confidence"] > 0.8

def test_classify_endpoint_empty_message():
    """Verify that an empty message body fails input validation."""
    payload = {
        "message": ""
    }
    response = client.post("/classify", json=payload)
    assert response.status_code == 422
