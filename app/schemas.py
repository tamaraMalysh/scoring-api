"""Pydantic schemas for request and response models."""

from pydantic import BaseModel, Field, field_validator


class ScoreRequest(BaseModel):
    """Request model for credit scoring."""

    # Personal information
    age: int = Field(..., ge=18, le=100, description="Applicant age in years")
    income: float = Field(..., gt=0, description="Annual income in USD")

    # Credit history
    credit_history_years: int = Field(
        ..., ge=0, le=50, description="Years of credit history"
    )
    existing_loans: int = Field(..., ge=0, le=20, description="Number of existing loans")

    # Financial metrics
    debt_to_income_ratio: float = Field(
        ..., ge=0, le=1, description="Debt to income ratio (0-1)"
    )
    savings: float = Field(..., ge=0, description="Total savings in USD")

    # Employment
    employment_status: str = Field(
        ..., description="Employment status: employed, self_employed, unemployed"
    )
    employment_years: int = Field(..., ge=0, le=60, description="Years at current job")

    @field_validator("employment_status")
    @classmethod
    def validate_employment_status(cls, v: str) -> str:
        """Validate employment status."""
        allowed = ["employed", "self_employed", "unemployed"]
        if v.lower() not in allowed:
            raise ValueError(f"employment_status must be one of: {', '.join(allowed)}")
        return v.lower()


class ScoreResponse(BaseModel):
    """Response model for credit scoring."""

    score: int = Field(..., ge=300, le=850, description="Credit score (300-850)")
    decision: str = Field(..., description="Approval decision: approved, rejected, review")
    reason: str = Field(..., description="Explanation for the decision")
    risk_level: str = Field(..., description="Risk level: low, medium, high")
