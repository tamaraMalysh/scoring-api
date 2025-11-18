"""Unit tests for scoring logic and individual scoring functions."""

import pytest

from app.api import (
    AGE_OPTIMAL_BONUS,
    AGE_SENIOR_BONUS,
    AGE_YOUNG_PENALTY,
    BASE_SCORE,
    CREDIT_EXCELLENT_BONUS,
    CREDIT_FAIR_BONUS,
    CREDIT_GOOD_BONUS,
    CREDIT_POOR_PENALTY,
    DTI_EXCELLENT_BONUS,
    DTI_GOOD_BONUS,
    DTI_HIGH_PENALTY,
    DTI_MODERATE_PENALTY,
    EMPLOYED_BONUS,
    INCOME_EXCELLENT_BONUS,
    INCOME_GOOD_BONUS,
    INCOME_LOW_PENALTY,
    INCOME_MODERATE_BONUS,
    LOAN_PENALTY_PER_LOAN,
    SAVINGS_HIGH_BONUS,
    SAVINGS_LOW_BONUS,
    SAVINGS_MODERATE_BONUS,
    SELF_EMPLOYED_BONUS,
    UNEMPLOYED_PENALTY,
    ScoringFactors,
    calculate_loans_penalty,
    determine_decision,
    determine_risk_level,
    score_age,
    score_credit_history,
    score_debt_to_income_ratio,
    score_employment,
    score_income,
    score_savings,
)
from app.schemas import ScoreRequest


class TestScoringFactors:
    """Test the ScoringFactors dataclass."""

    def test_scoring_factors_initialization(self):
        """Test ScoringFactors can be initialized with defaults."""
        factors = ScoringFactors()
        assert factors.age_score == 0
        assert factors.income_score == 0
        assert factors.credit_history_score == 0

    def test_scoring_factors_total(self):
        """Test total calculation includes base score and all factors."""
        factors = ScoringFactors(
            age_score=30,
            income_score=50,
            credit_history_score=30,
            debt_to_income_score=40,
            savings_score=30,
            employment_score=30,
            loans_penalty=-20,
        )
        # BASE_SCORE + 30 + 50 + 30 + 40 + 30 + 30 - 20 = 600 + 190 = 790
        assert factors.total() == BASE_SCORE + 190

    def test_scoring_factors_with_penalties(self):
        """Test total calculation with negative scores."""
        factors = ScoringFactors(
            age_score=-20,
            income_score=-30,
            loans_penalty=-50,
        )
        assert factors.total() == BASE_SCORE - 100


class TestAgeScoring:
    """Test age scoring function."""

    @pytest.mark.parametrize(
        "age,expected_score",
        [
            (25, AGE_OPTIMAL_BONUS),  # Lower boundary of optimal range
            (35, AGE_OPTIMAL_BONUS),  # Mid-range optimal
            (55, AGE_OPTIMAL_BONUS),  # Upper boundary of optimal range
            (20, AGE_YOUNG_PENALTY),  # Too young
            (18, AGE_YOUNG_PENALTY),  # Minimum age
            (60, AGE_SENIOR_BONUS),   # Senior
            (75, AGE_SENIOR_BONUS),   # Elderly
        ],
    )
    def test_age_scoring(self, age, expected_score):
        """Test age scoring across different age ranges."""
        assert score_age(age) == expected_score


class TestIncomeScoring:
    """Test income scoring function."""

    @pytest.mark.parametrize(
        "income,expected_score",
        [
            (150000, INCOME_EXCELLENT_BONUS),  # Excellent income
            (100000, INCOME_EXCELLENT_BONUS),  # Boundary excellent
            (75000, INCOME_GOOD_BONUS),        # Good income
            (60000, INCOME_GOOD_BONUS),        # Boundary good
            (50000, INCOME_MODERATE_BONUS),    # Moderate income
            (40000, INCOME_MODERATE_BONUS),    # Boundary moderate
            (30000, INCOME_LOW_PENALTY),       # Low income
            (15000, INCOME_LOW_PENALTY),       # Very low income
        ],
    )
    def test_income_scoring(self, income, expected_score):
        """Test income scoring across different income levels."""
        assert score_income(income) == expected_score


class TestCreditHistoryScoring:
    """Test credit history scoring function."""

    @pytest.mark.parametrize(
        "years,expected_score",
        [
            (15, CREDIT_EXCELLENT_BONUS),  # Excellent history
            (10, CREDIT_EXCELLENT_BONUS),  # Boundary excellent
            (7, CREDIT_GOOD_BONUS),        # Good history
            (5, CREDIT_GOOD_BONUS),        # Boundary good
            (3, CREDIT_FAIR_BONUS),        # Fair history
            (2, CREDIT_FAIR_BONUS),        # Boundary fair
            (1, CREDIT_POOR_PENALTY),      # Poor history
            (0, CREDIT_POOR_PENALTY),      # No history
        ],
    )
    def test_credit_history_scoring(self, years, expected_score):
        """Test credit history scoring across different durations."""
        assert score_credit_history(years) == expected_score


class TestDebtToIncomeScoring:
    """Test debt-to-income ratio scoring function."""

    @pytest.mark.parametrize(
        "ratio,expected_score",
        [
            (0.1, DTI_EXCELLENT_BONUS),   # Excellent ratio
            (0.2, DTI_EXCELLENT_BONUS),   # Boundary excellent
            (0.25, DTI_GOOD_BONUS),       # Good ratio
            (0.35, DTI_GOOD_BONUS),       # Boundary good
            (0.4, DTI_MODERATE_PENALTY),  # Moderate ratio
            (0.5, DTI_MODERATE_PENALTY),  # Boundary moderate
            (0.7, DTI_HIGH_PENALTY),      # High ratio
            (0.9, DTI_HIGH_PENALTY),      # Very high ratio
        ],
    )
    def test_debt_to_income_scoring(self, ratio, expected_score):
        """Test DTI scoring across different ratios."""
        assert score_debt_to_income_ratio(ratio) == expected_score


class TestSavingsScoring:
    """Test savings scoring function."""

    @pytest.mark.parametrize(
        "savings,expected_score",
        [
            (80000, SAVINGS_HIGH_BONUS),      # High savings
            (50000, SAVINGS_HIGH_BONUS),      # Boundary high
            (30000, SAVINGS_MODERATE_BONUS),  # Moderate savings
            (20000, SAVINGS_MODERATE_BONUS),  # Boundary moderate
            (15000, SAVINGS_LOW_BONUS),       # Low savings
            (10000, SAVINGS_LOW_BONUS),       # Boundary low
            (5000, 0),                        # Very low savings
            (0, 0),                           # No savings
        ],
    )
    def test_savings_scoring(self, savings, expected_score):
        """Test savings scoring across different amounts."""
        assert score_savings(savings) == expected_score


class TestEmploymentScoring:
    """Test employment scoring function."""

    @pytest.mark.parametrize(
        "status,years,expected_score",
        [
            ("employed", 5, EMPLOYED_BONUS),                 # Good employment
            ("employed", 3, EMPLOYED_BONUS),                 # Boundary employed
            ("employed", 2, 0),                              # Employed but short tenure
            ("self_employed", 10, SELF_EMPLOYED_BONUS),      # Good self-employment
            ("self_employed", 5, SELF_EMPLOYED_BONUS),       # Boundary self-employed
            ("self_employed", 3, 0),                         # Self-employed but short
            ("unemployed", 0, UNEMPLOYED_PENALTY),           # Unemployed
            ("unemployed", 5, UNEMPLOYED_PENALTY),           # Unemployed (years ignored)
        ],
    )
    def test_employment_scoring(self, status, years, expected_score):
        """Test employment scoring across different statuses and tenures."""
        assert score_employment(status, years) == expected_score


class TestLoansPenalty:
    """Test loans penalty calculation."""

    @pytest.mark.parametrize(
        "num_loans,expected_penalty",
        [
            (0, 0),
            (1, -LOAN_PENALTY_PER_LOAN),
            (2, -2 * LOAN_PENALTY_PER_LOAN),
            (5, -5 * LOAN_PENALTY_PER_LOAN),
            (10, -10 * LOAN_PENALTY_PER_LOAN),
        ],
    )
    def test_loans_penalty(self, num_loans, expected_penalty):
        """Test loans penalty calculation."""
        assert calculate_loans_penalty(num_loans) == expected_penalty


class TestDecisionLogic:
    """Test decision determination logic."""

    def test_determine_decision_approved(self):
        """Test that high scores result in approved decision."""
        assert determine_decision(700) == "approved"
        assert determine_decision(650) == "approved"  # Boundary

    def test_determine_decision_review(self):
        """Test that moderate scores result in review decision."""
        assert determine_decision(600) == "review"
        assert determine_decision(550) == "review"  # Boundary

    def test_determine_decision_rejected(self):
        """Test that low scores result in rejected decision."""
        assert determine_decision(500) == "rejected"
        assert determine_decision(300) == "rejected"


class TestRiskLevel:
    """Test risk level determination."""

    @pytest.mark.parametrize(
        "decision,expected_risk",
        [
            ("approved", "low"),
            ("review", "medium"),
            ("rejected", "high"),
        ],
    )
    def test_determine_risk_level(self, decision, expected_risk):
        """Test risk level mapping from decisions."""
        assert determine_risk_level(decision) == expected_risk


class TestEndToEndScoring:
    """Test end-to-end scoring with realistic scenarios."""

    def test_excellent_profile_scoring(self):
        """Test that excellent profile gets high score."""
        from app.api import calculate_score

        request = ScoreRequest(
            age=40,
            income=120000,
            credit_history_years=12,
            existing_loans=0,
            debt_to_income_ratio=0.15,
            savings=60000,
            employment_status="employed",
            employment_years=8,
        )
        result = calculate_score(request)

        assert result.score >= 700
        assert result.decision == "approved"
        assert result.risk_level == "low"
        assert "Strong" in result.reason or "strong" in result.reason.lower()

    def test_poor_profile_scoring(self):
        """Test that poor profile gets low score."""
        from app.api import calculate_score

        request = ScoreRequest(
            age=20,
            income=20000,
            credit_history_years=0,
            existing_loans=6,
            debt_to_income_ratio=0.8,
            savings=0,
            employment_status="unemployed",
            employment_years=0,
        )
        result = calculate_score(request)

        assert result.score < 550
        assert result.decision == "rejected"
        assert result.risk_level == "high"

    def test_score_clamping_min(self):
        """Test that score is clamped to minimum value."""
        from app.api import calculate_score
        from app.core.config import settings

        request = ScoreRequest(
            age=18,
            income=15000,
            credit_history_years=0,
            existing_loans=10,  # Heavy penalty
            debt_to_income_ratio=0.95,
            savings=0,
            employment_status="unemployed",
            employment_years=0,
        )
        result = calculate_score(request)

        assert result.score >= settings.min_score

    def test_score_clamping_max(self):
        """Test that score is clamped to maximum value."""
        from app.api import calculate_score
        from app.core.config import settings

        request = ScoreRequest(
            age=40,
            income=200000,  # Very high
            credit_history_years=20,
            existing_loans=0,
            debt_to_income_ratio=0.05,
            savings=100000,
            employment_status="employed",
            employment_years=15,
        )
        result = calculate_score(request)

        assert result.score <= settings.max_score
