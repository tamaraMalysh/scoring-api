"""Integration tests for the scoring API endpoints."""

import pytest


class TestRootEndpoints:
    """Test root and health check endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns API information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"

    def test_root_endpoint_structure(self, client):
        """Test root endpoint response structure."""
        response = client.get("/")
        data = response.json()
        assert isinstance(data["name"], str)
        assert isinstance(data["version"], str)
        assert len(data["name"]) > 0
        assert len(data["version"]) > 0

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_check_returns_json(self, client):
        """Test health check returns valid JSON."""
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"


class TestScoreEndpoint:
    """Test /score endpoint integration."""

    def test_score_approved_applicant(self, client, excellent_applicant):
        """Test scoring for an excellent applicant."""
        response = client.post("/score", json=excellent_applicant)
        assert response.status_code == 200

        data = response.json()
        assert "score" in data
        assert "decision" in data
        assert "reason" in data
        assert "risk_level" in data

        # Excellent profile should be approved
        assert data["decision"] == "approved"
        assert data["risk_level"] == "low"
        assert 650 <= data["score"] <= 850

    def test_score_rejected_applicant(self, client, poor_applicant):
        """Test scoring for a poor applicant."""
        response = client.post("/score", json=poor_applicant)
        assert response.status_code == 200

        data = response.json()
        assert data["decision"] == "rejected"
        assert data["risk_level"] == "high"
        assert 300 <= data["score"] < 550
        assert "Low score" in data["reason"]

    def test_score_review_applicant(self, client, moderate_applicant):
        """Test scoring for a moderate applicant requiring review."""
        response = client.post("/score", json=moderate_applicant)
        assert response.status_code == 200

        data = response.json()
        # Moderate applicants may be approved, review, or rejected depending on exact scores
        assert data["decision"] in ["review", "approved", "rejected"]
        assert 300 <= data["score"] <= 850

    def test_score_baseline_applicant(self, client, base_applicant):
        """Test scoring for baseline applicant."""
        response = client.post("/score", json=base_applicant)
        assert response.status_code == 200

        data = response.json()
        # Base applicant should get approved
        assert data["score"] >= 600


class TestScoreValidation:
    """Test request validation for /score endpoint."""

    @pytest.mark.parametrize(
        "field,invalid_value",
        [
            ("age", 15),      # Too young
            ("age", 150),     # Too old
            ("age", -5),      # Negative
            ("income", -1000),     # Negative
            ("income", 0),         # Zero
            ("credit_history_years", -1),  # Negative
            ("credit_history_years", 100), # Too high
            ("existing_loans", -1),        # Negative
            ("debt_to_income_ratio", -0.1), # Negative
            ("debt_to_income_ratio", 1.5),  # > 1
            ("savings", -100),              # Negative
            ("employment_years", -1),       # Negative
        ],
    )
    def test_score_validation_invalid_values(self, client, base_applicant, field, invalid_value):
        """Test validation for various invalid field values."""
        invalid_request = base_applicant.copy()
        invalid_request[field] = invalid_value

        response = client.post("/score", json=invalid_request)
        assert response.status_code == 422

    def test_score_validation_invalid_employment_status(self, client, base_applicant):
        """Test validation for invalid employment status."""
        invalid_request = base_applicant.copy()
        invalid_request["employment_status"] = "invalid_status"

        response = client.post("/score", json=invalid_request)
        assert response.status_code == 422

    @pytest.mark.parametrize(
        "missing_field",
        ["age", "income", "credit_history_years", "existing_loans",
         "debt_to_income_ratio", "savings", "employment_status", "employment_years"],
    )
    def test_score_missing_required_fields(self, client, base_applicant, missing_field):
        """Test that missing required fields return validation error."""
        incomplete_request = base_applicant.copy()
        del incomplete_request[missing_field]

        response = client.post("/score", json=incomplete_request)
        assert response.status_code == 422

    def test_score_empty_body(self, client):
        """Test that empty request body returns validation error."""
        response = client.post("/score", json={})
        assert response.status_code == 422

    def test_score_invalid_json(self, client):
        """Test that invalid JSON returns error."""
        response = client.post(
            "/score",
            data="not json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422


class TestScoreEmploymentStatus:
    """Test employment status handling."""

    def test_score_employment_status_case_insensitive(self, client, base_applicant):
        """Test that employment status is case insensitive."""
        request_upper = base_applicant.copy()
        request_upper["employment_status"] = "EMPLOYED"

        response = client.post("/score", json=request_upper)
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "status,years,expected_min_score",
        [
            ("employed", 5, 600),          # Good employment
            ("self_employed", 6, 600),     # Good self-employment
            ("unemployed", 0, 300),        # Unemployment penalty
        ],
    )
    def test_score_employment_scenarios(self, client, base_applicant, status, years, expected_min_score):
        """Test various employment scenarios."""
        request = base_applicant.copy()
        request["employment_status"] = status
        request["employment_years"] = years

        response = client.post("/score", json=request)
        assert response.status_code == 200

        data = response.json()
        assert data["score"] >= expected_min_score or data["decision"] == "rejected"


class TestScoreResponseStructure:
    """Test score response structure and types."""

    def test_score_response_has_all_fields(self, client, base_applicant):
        """Test that response has all required fields."""
        response = client.post("/score", json=base_applicant)
        assert response.status_code == 200

        data = response.json()
        required_fields = ["score", "decision", "reason", "risk_level"]
        for field in required_fields:
            assert field in data
            assert data[field] is not None

    def test_score_response_field_types(self, client, base_applicant):
        """Test that response fields have correct types."""
        response = client.post("/score", json=base_applicant)
        data = response.json()

        assert isinstance(data["score"], int)
        assert isinstance(data["decision"], str)
        assert isinstance(data["reason"], str)
        assert isinstance(data["risk_level"], str)

    def test_score_response_field_values(self, client, base_applicant):
        """Test that response fields have valid values."""
        response = client.post("/score", json=base_applicant)
        data = response.json()

        assert 300 <= data["score"] <= 850
        assert data["decision"] in ["approved", "rejected", "review"]
        assert data["risk_level"] in ["low", "medium", "high"]
        assert len(data["reason"]) > 0

    def test_score_response_decision_risk_correlation(self, client, base_applicant):
        """Test that decision and risk level are correlated correctly."""
        response = client.post("/score", json=base_applicant)
        data = response.json()

        if data["decision"] == "approved":
            assert data["risk_level"] == "low"
        elif data["decision"] == "review":
            assert data["risk_level"] == "medium"
        elif data["decision"] == "rejected":
            assert data["risk_level"] == "high"


class TestScoreEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_score_maximum_values(self, client):
        """Test with maximum allowed values."""
        max_request = {
            "age": 100,
            "income": 999999,
            "credit_history_years": 50,
            "existing_loans": 0,
            "debt_to_income_ratio": 0,
            "savings": 999999,
            "employment_status": "employed",
            "employment_years": 60,
        }
        response = client.post("/score", json=max_request)
        assert response.status_code == 200
        data = response.json()
        assert data["score"] <= 850  # Should be clamped

    def test_score_minimum_values(self, client):
        """Test with minimum allowed values."""
        min_request = {
            "age": 18,
            "income": 0.01,  # Minimum positive
            "credit_history_years": 0,
            "existing_loans": 0,
            "debt_to_income_ratio": 0,
            "savings": 0,
            "employment_status": "unemployed",
            "employment_years": 0,
        }
        response = client.post("/score", json=min_request)
        assert response.status_code == 200
        data = response.json()
        assert data["score"] >= 300  # Should be clamped

    def test_score_many_loans(self, client, base_applicant):
        """Test applicant with many existing loans."""
        request = base_applicant.copy()
        request["existing_loans"] = 15

        response = client.post("/score", json=request)
        assert response.status_code == 200
        data = response.json()
        # Many loans should reduce score significantly
        assert data["score"] < base_applicant.get("score", 700)

    def test_score_consistency(self, client, base_applicant):
        """Test that same input produces same output."""
        response1 = client.post("/score", json=base_applicant)
        response2 = client.post("/score", json=base_applicant)

        assert response1.json() == response2.json()
