"""Pytest configuration and shared fixtures for tests."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def base_applicant():
    """Provide a baseline applicant profile for testing."""
    return {
        "age": 35,
        "income": 75000,
        "credit_history_years": 8,
        "existing_loans": 2,
        "debt_to_income_ratio": 0.25,
        "savings": 25000,
        "employment_status": "employed",
        "employment_years": 5,
    }


@pytest.fixture
def excellent_applicant():
    """Provide an excellent applicant profile (should be approved)."""
    return {
        "age": 42,
        "income": 120000,
        "credit_history_years": 12,
        "existing_loans": 1,
        "debt_to_income_ratio": 0.15,
        "savings": 60000,
        "employment_status": "employed",
        "employment_years": 8,
    }


@pytest.fixture
def poor_applicant():
    """Provide a poor applicant profile (should be rejected)."""
    return {
        "age": 22,
        "income": 25000,
        "credit_history_years": 0,
        "existing_loans": 5,
        "debt_to_income_ratio": 0.75,
        "savings": 500,
        "employment_status": "unemployed",
        "employment_years": 0,
    }


@pytest.fixture
def moderate_applicant():
    """Provide a moderate applicant profile (likely review)."""
    return {
        "age": 28,
        "income": 45000,
        "credit_history_years": 2,
        "existing_loans": 3,
        "debt_to_income_ratio": 0.4,
        "savings": 5000,
        "employment_status": "employed",
        "employment_years": 2,
    }
