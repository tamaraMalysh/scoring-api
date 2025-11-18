"""Tests for the scoring API endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestRootEndpoints:
    """Test root and health check endpoints."""

    def test_root_endpoint(self):
        """Test root endpoint returns API information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"

    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestScoreEndpoint:
    """Test /score endpoint."""

    @pytest.fixture
    def valid_request(self):
        """Fixture providing a valid score request."""
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

    def test_score_approved_applicant(self, valid_request):
        """Test scoring for a strong applicant."""
        response = client.post("/score", json=valid_request)
        assert response.status_code == 200

        data = response.json()
        assert "score" in data
        assert "decision" in data
        assert "reason" in data
        assert "risk_level" in data

        # Strong profile should be approved
        assert data["decision"] == "approved"
        assert data["risk_level"] == "low"
        assert 650 <= data["score"] <= 850

    def test_score_rejected_applicant(self, valid_request):
        """Test scoring for a weak applicant."""
        weak_request = valid_request.copy()
        weak_request.update(
            {
                "income": 20000,
                "credit_history_years": 0,
                "debt_to_income_ratio": 0.7,
                "employment_status": "unemployed",
                "existing_loans": 5,
                "savings": 0,
            }
        )

        response = client.post("/score", json=weak_request)
        assert response.status_code == 200

        data = response.json()
        assert data["decision"] == "rejected"
        assert data["risk_level"] == "high"
        assert 300 <= data["score"] < 550

    def test_score_review_applicant(self, valid_request):
        """Test scoring for a moderate applicant requiring review."""
        moderate_request = valid_request.copy()
        moderate_request.update(
            {
                "income": 45000,
                "credit_history_years": 2,
                "debt_to_income_ratio": 0.4,
                "savings": 5000,
            }
        )

        response = client.post("/score", json=moderate_request)
        assert response.status_code == 200

        data = response.json()
        assert data["decision"] in ["review", "approved", "rejected"]
        assert 300 <= data["score"] <= 850

    def test_score_high_income_applicant(self, valid_request):
        """Test that high income positively affects score."""
        high_income_request = valid_request.copy()
        high_income_request["income"] = 150000

        response = client.post("/score", json=high_income_request)
        assert response.status_code == 200

        data = response.json()
        # High income should generally lead to approval
        assert data["score"] >= 650

    def test_score_validation_age_too_young(self, valid_request):
        """Test validation for age below minimum."""
        invalid_request = valid_request.copy()
        invalid_request["age"] = 15

        response = client.post("/score", json=invalid_request)
        assert response.status_code == 422  # Validation error

    def test_score_validation_age_too_old(self, valid_request):
        """Test validation for age above maximum."""
        invalid_request = valid_request.copy()
        invalid_request["age"] = 150

        response = client.post("/score", json=invalid_request)
        assert response.status_code == 422

    def test_score_validation_negative_income(self, valid_request):
        """Test validation for negative income."""
        invalid_request = valid_request.copy()
        invalid_request["income"] = -1000

        response = client.post("/score", json=invalid_request)
        assert response.status_code == 422

    def test_score_validation_invalid_employment_status(self, valid_request):
        """Test validation for invalid employment status."""
        invalid_request = valid_request.copy()
        invalid_request["employment_status"] = "invalid_status"

        response = client.post("/score", json=invalid_request)
        assert response.status_code == 422

    def test_score_validation_debt_ratio_out_of_range(self, valid_request):
        """Test validation for debt ratio outside 0-1 range."""
        invalid_request = valid_request.copy()
        invalid_request["debt_to_income_ratio"] = 1.5

        response = client.post("/score", json=invalid_request)
        assert response.status_code == 422

    def test_score_missing_required_field(self, valid_request):
        """Test that missing required fields return validation error."""
        incomplete_request = valid_request.copy()
        del incomplete_request["age"]

        response = client.post("/score", json=incomplete_request)
        assert response.status_code == 422

    def test_score_employment_status_case_insensitive(self, valid_request):
        """Test that employment status is case insensitive."""
        request_upper = valid_request.copy()
        request_upper["employment_status"] = "EMPLOYED"

        response = client.post("/score", json=request_upper)
        assert response.status_code == 200

    def test_score_self_employed_applicant(self, valid_request):
        """Test scoring for self-employed applicant."""
        self_employed_request = valid_request.copy()
        self_employed_request["employment_status"] = "self_employed"
        self_employed_request["employment_years"] = 6

        response = client.post("/score", json=self_employed_request)
        assert response.status_code == 200

        data = response.json()
        assert 300 <= data["score"] <= 850
        assert data["decision"] in ["approved", "review", "rejected"]

    def test_score_response_structure(self, valid_request):
        """Test that response has all required fields."""
        response = client.post("/score", json=valid_request)
        assert response.status_code == 200

        data = response.json()
        required_fields = ["score", "decision", "reason", "risk_level"]
        for field in required_fields:
            assert field in data
            assert data[field] is not None

        # Check field types and ranges
        assert isinstance(data["score"], int)
        assert 300 <= data["score"] <= 850
        assert data["decision"] in ["approved", "rejected", "review"]
        assert data["risk_level"] in ["low", "medium", "high"]
        assert isinstance(data["reason"], str)
        assert len(data["reason"]) > 0
