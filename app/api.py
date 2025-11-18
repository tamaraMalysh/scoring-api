"""API endpoints for the scoring service."""

import logging
from dataclasses import dataclass
from typing import Literal

from fastapi import APIRouter

from app.core.config import settings
from app.schemas import ScoreRequest, ScoreResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# Base score
BASE_SCORE = 600

# Age scoring constants
AGE_OPTIMAL_MIN = 25
AGE_OPTIMAL_MAX = 55
AGE_OPTIMAL_BONUS = 30
AGE_YOUNG_PENALTY = -20
AGE_SENIOR_BONUS = 10

# Income thresholds and scores
INCOME_EXCELLENT_THRESHOLD = 100000
INCOME_EXCELLENT_BONUS = 50
INCOME_GOOD_THRESHOLD = 60000
INCOME_GOOD_BONUS = 30
INCOME_MODERATE_THRESHOLD = 40000
INCOME_MODERATE_BONUS = 10
INCOME_LOW_PENALTY = -30

# Credit history thresholds and scores
CREDIT_EXCELLENT_YEARS = 10
CREDIT_EXCELLENT_BONUS = 50
CREDIT_GOOD_YEARS = 5
CREDIT_GOOD_BONUS = 30
CREDIT_FAIR_YEARS = 2
CREDIT_FAIR_BONUS = 10
CREDIT_POOR_PENALTY = -20

# Debt-to-income ratio thresholds and scores
DTI_EXCELLENT_THRESHOLD = 0.2
DTI_EXCELLENT_BONUS = 40
DTI_GOOD_THRESHOLD = 0.35
DTI_GOOD_BONUS = 20
DTI_MODERATE_THRESHOLD = 0.5
DTI_MODERATE_PENALTY = -10
DTI_HIGH_PENALTY = -50

# Savings thresholds and scores
SAVINGS_HIGH_THRESHOLD = 50000
SAVINGS_HIGH_BONUS = 30
SAVINGS_MODERATE_THRESHOLD = 20000
SAVINGS_MODERATE_BONUS = 20
SAVINGS_LOW_THRESHOLD = 10000
SAVINGS_LOW_BONUS = 10

# Employment thresholds and scores
EMPLOYED_MIN_YEARS = 3
EMPLOYED_BONUS = 30
SELF_EMPLOYED_MIN_YEARS = 5
SELF_EMPLOYED_BONUS = 20
UNEMPLOYED_PENALTY = -40

# Loan penalty
LOAN_PENALTY_PER_LOAN = 10

# Decision thresholds
REVIEW_THRESHOLD = 550

# Reason message thresholds
REASON_INCOME_GOOD_THRESHOLD = 60000
REASON_DTI_HEALTHY_THRESHOLD = 0.35
REASON_DTI_HIGH_THRESHOLD = 0.5
REASON_CREDIT_SOLID_YEARS = 5
REASON_CREDIT_LIMITED_YEARS = 3
REASON_CREDIT_INSUFFICIENT_YEARS = 2


@dataclass
class ScoringFactors:
    """Container for individual scoring factor contributions."""

    age_score: int = 0
    income_score: int = 0
    credit_history_score: int = 0
    debt_to_income_score: int = 0
    savings_score: int = 0
    employment_score: int = 0
    loans_penalty: int = 0

    def total(self) -> int:
        """Calculate total score from all factors."""
        return (
            BASE_SCORE
            + self.age_score
            + self.income_score
            + self.credit_history_score
            + self.debt_to_income_score
            + self.savings_score
            + self.employment_score
            + self.loans_penalty
        )


def score_age(age: int) -> int:
    """
    Calculate age factor score.

    Optimal age range is 25-55 years.
    """
    if AGE_OPTIMAL_MIN <= age <= AGE_OPTIMAL_MAX:
        return AGE_OPTIMAL_BONUS
    elif age < AGE_OPTIMAL_MIN:
        return AGE_YOUNG_PENALTY
    else:
        return AGE_SENIOR_BONUS


def score_income(income: float) -> int:
    """
    Calculate income factor score.

    Higher income provides better score.
    """
    if income >= INCOME_EXCELLENT_THRESHOLD:
        return INCOME_EXCELLENT_BONUS
    elif income >= INCOME_GOOD_THRESHOLD:
        return INCOME_GOOD_BONUS
    elif income >= INCOME_MODERATE_THRESHOLD:
        return INCOME_MODERATE_BONUS
    else:
        return INCOME_LOW_PENALTY


def score_credit_history(years: int) -> int:
    """
    Calculate credit history factor score.

    Longer credit history is better.
    """
    if years >= CREDIT_EXCELLENT_YEARS:
        return CREDIT_EXCELLENT_BONUS
    elif years >= CREDIT_GOOD_YEARS:
        return CREDIT_GOOD_BONUS
    elif years >= CREDIT_FAIR_YEARS:
        return CREDIT_FAIR_BONUS
    else:
        return CREDIT_POOR_PENALTY


def score_debt_to_income_ratio(ratio: float) -> int:
    """
    Calculate debt-to-income ratio score.

    Lower ratio is better.
    """
    if ratio <= DTI_EXCELLENT_THRESHOLD:
        return DTI_EXCELLENT_BONUS
    elif ratio <= DTI_GOOD_THRESHOLD:
        return DTI_GOOD_BONUS
    elif ratio <= DTI_MODERATE_THRESHOLD:
        return DTI_MODERATE_PENALTY
    else:
        return DTI_HIGH_PENALTY


def score_savings(savings: float) -> int:
    """
    Calculate savings factor score.

    Higher savings provide better score.
    """
    if savings >= SAVINGS_HIGH_THRESHOLD:
        return SAVINGS_HIGH_BONUS
    elif savings >= SAVINGS_MODERATE_THRESHOLD:
        return SAVINGS_MODERATE_BONUS
    elif savings >= SAVINGS_LOW_THRESHOLD:
        return SAVINGS_LOW_BONUS
    else:
        return 0


def score_employment(status: str, years: int) -> int:
    """
    Calculate employment factor score.

    Stable employment with sufficient tenure is rewarded.
    """
    if status == "employed" and years >= EMPLOYED_MIN_YEARS:
        return EMPLOYED_BONUS
    elif status == "self_employed" and years >= SELF_EMPLOYED_MIN_YEARS:
        return SELF_EMPLOYED_BONUS
    elif status == "unemployed":
        return UNEMPLOYED_PENALTY
    else:
        return 0


def calculate_loans_penalty(num_loans: int) -> int:
    """
    Calculate penalty for existing loans.

    Each loan reduces the score.
    """
    return -num_loans * LOAN_PENALTY_PER_LOAN


def determine_decision(
    score: int,
) -> Literal["approved", "review", "rejected"]:
    """
    Determine approval decision based on score.

    Returns:
        "approved" for high scores
        "review" for moderate scores
        "rejected" for low scores
    """
    if score >= settings.approval_threshold:
        return "approved"
    elif score >= REVIEW_THRESHOLD:
        return "review"
    else:
        return "rejected"


def determine_risk_level(
    decision: Literal["approved", "review", "rejected"]
) -> Literal["low", "medium", "high"]:
    """
    Determine risk level based on decision.

    Returns:
        "low" for approved applicants
        "medium" for review cases
        "high" for rejected applicants
    """
    risk_map = {
        "approved": "low",
        "review": "medium",
        "rejected": "high",
    }
    return risk_map[decision]


def build_reason(
    score: int,
    decision: Literal["approved", "review", "rejected"],
    request: ScoreRequest,
) -> str:
    """
    Build explanation reason based on decision and applicant profile.

    Args:
        score: Calculated credit score
        decision: Approval decision
        request: Original score request with applicant data

    Returns:
        Human-readable explanation string
    """
    if decision == "approved":
        return _build_approved_reason(score, request)
    elif decision == "review":
        return _build_review_reason(score, request)
    else:
        return _build_rejected_reason(score, request)


def _build_approved_reason(score: int, request: ScoreRequest) -> str:
    """Build reason for approved decision."""
    reason_parts = [f"Strong financial profile with score {score}."]

    if request.income >= REASON_INCOME_GOOD_THRESHOLD:
        reason_parts.append("Good income level.")
    if request.debt_to_income_ratio <= REASON_DTI_HEALTHY_THRESHOLD:
        reason_parts.append("Healthy debt-to-income ratio.")
    if request.credit_history_years >= REASON_CREDIT_SOLID_YEARS:
        reason_parts.append("Solid credit history.")

    return " ".join(reason_parts)


def _build_review_reason(score: int, request: ScoreRequest) -> str:
    """Build reason for review decision."""
    reason_parts = [f"Moderate score of {score} requires manual review."]

    if request.debt_to_income_ratio > REASON_DTI_HEALTHY_THRESHOLD:
        reason_parts.append("Consider reducing debt-to-income ratio.")
    if request.credit_history_years < REASON_CREDIT_LIMITED_YEARS:
        reason_parts.append("Limited credit history.")

    return " ".join(reason_parts)


def _build_rejected_reason(score: int, request: ScoreRequest) -> str:
    """Build reason for rejected decision."""
    reason_parts = [f"Low score of {score}."]

    if request.debt_to_income_ratio > REASON_DTI_HIGH_THRESHOLD:
        reason_parts.append("High debt-to-income ratio.")
    if request.employment_status == "unemployed":
        reason_parts.append("Unemployment concerns.")
    if request.credit_history_years < REASON_CREDIT_INSUFFICIENT_YEARS:
        reason_parts.append("Insufficient credit history.")

    return " ".join(reason_parts)


def calculate_score(request: ScoreRequest) -> ScoreResponse:
    """
    Calculate credit score based on applicant features.

    This function orchestrates the scoring process by:
    1. Calculating individual factor scores
    2. Computing total score
    3. Determining decision and risk level
    4. Building explanation reason

    Args:
        request: ScoreRequest containing applicant features

    Returns:
        ScoreResponse with score, decision, reason, and risk level
    """
    # Calculate individual scoring factors
    factors = ScoringFactors(
        age_score=score_age(request.age),
        income_score=score_income(request.income),
        credit_history_score=score_credit_history(request.credit_history_years),
        debt_to_income_score=score_debt_to_income_ratio(request.debt_to_income_ratio),
        savings_score=score_savings(request.savings),
        employment_score=score_employment(request.employment_status, request.employment_years),
        loans_penalty=calculate_loans_penalty(request.existing_loans),
    )

    # Calculate total score and clamp to valid range
    total_score = factors.total()
    clamped_score = max(settings.min_score, min(settings.max_score, total_score))

    # Determine decision and risk level
    decision = determine_decision(clamped_score)
    risk_level = determine_risk_level(decision)

    # Build explanation reason
    reason = build_reason(clamped_score, decision, request)

    return ScoreResponse(
        score=clamped_score,
        decision=decision,
        reason=reason,
        risk_level=risk_level,
    )


@router.post("/score", response_model=ScoreResponse)
async def score_applicant(request: ScoreRequest) -> ScoreResponse:
    """
    Score a credit applicant based on their financial profile.

    Args:
        request: ScoreRequest containing applicant features

    Returns:
        ScoreResponse with score, decision, reason, and risk level
    """
    logger.info(f"Scoring request for applicant: age={request.age}, income={request.income}")

    result = calculate_score(request)

    logger.info(
        f"Score calculated: {result.score}, "
        f"decision={result.decision} risk_level={result.risk_level}"
    )

    return result
