"""Load testing scenarios for the scoring API using Locust.

Run with:
    locust --host=http://localhost:8000

Or headless mode:
    locust --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 60s --headless
"""

import random

from locust import HttpUser, between, task


class ScoringAPIUser(HttpUser):
    """
    Simulates a user hitting the scoring API.

    Each user waits between 1-3 seconds between requests to simulate realistic usage.
    """

    wait_time = between(1, 3)

    def on_start(self):
        """Called when a user starts. Can be used for setup like authentication."""
        # Health check to ensure API is available
        self.client.get("/health")

    @task(3)
    def score_approved_applicant(self):
        """
        Test scoring endpoint with a strong applicant profile.

        Weight: 3 (will be called 3x more often than other tasks)
        Expected: Approved decision with low risk
        """
        payload = {
            "age": random.randint(30, 50),
            "income": random.randint(70000, 150000),
            "credit_history_years": random.randint(5, 15),
            "existing_loans": random.randint(0, 2),
            "debt_to_income_ratio": random.uniform(0.1, 0.3),
            "savings": random.randint(20000, 80000),
            "employment_status": "employed",
            "employment_years": random.randint(3, 15),
        }

        with self.client.post(
            "/score",
            json=payload,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("decision") == "approved":
                    response.success()
                else:
                    response.failure(f"Expected approved, got {data.get('decision')}")
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(2)
    def score_moderate_applicant(self):
        """
        Test scoring endpoint with a moderate applicant profile.

        Weight: 2
        Expected: Review or approved decision with medium risk
        """
        payload = {
            "age": random.randint(25, 40),
            "income": random.randint(40000, 70000),
            "credit_history_years": random.randint(2, 5),
            "existing_loans": random.randint(2, 4),
            "debt_to_income_ratio": random.uniform(0.3, 0.45),
            "savings": random.randint(5000, 20000),
            "employment_status": random.choice(["employed", "self_employed"]),
            "employment_years": random.randint(2, 6),
        }

        with self.client.post(
            "/score",
            json=payload,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(1)
    def score_weak_applicant(self):
        """
        Test scoring endpoint with a weak applicant profile.

        Weight: 1
        Expected: Rejected decision with high risk
        """
        payload = {
            "age": random.randint(18, 25),
            "income": random.randint(15000, 35000),
            "credit_history_years": random.randint(0, 2),
            "existing_loans": random.randint(3, 6),
            "debt_to_income_ratio": random.uniform(0.5, 0.8),
            "savings": random.randint(0, 5000),
            "employment_status": random.choice(["employed", "unemployed"]),
            "employment_years": random.randint(0, 2),
        }

        with self.client.post(
            "/score",
            json=payload,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(1)
    def score_random_applicant(self):
        """
        Test scoring endpoint with completely random data.

        Weight: 1
        Tests the full range of possible inputs
        """
        payload = {
            "age": random.randint(18, 75),
            "income": random.uniform(15000, 200000),
            "credit_history_years": random.randint(0, 30),
            "existing_loans": random.randint(0, 10),
            "debt_to_income_ratio": random.uniform(0, 0.9),
            "savings": random.uniform(0, 100000),
            "employment_status": random.choice(["employed", "self_employed", "unemployed"]),
            "employment_years": random.randint(0, 40),
        }

        with self.client.post(
            "/score",
            json=payload,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(1)
    def test_validation_error(self):
        """
        Test API validation with invalid data.

        Weight: 1
        Expected: 422 validation error
        """
        payload = {
            "age": -5,  # Invalid: negative age
            "income": 50000,
            "credit_history_years": 5,
            "existing_loans": 2,
            "debt_to_income_ratio": 0.3,
            "savings": 10000,
            "employment_status": "employed",
            "employment_years": 3,
        }

        with self.client.post(
            "/score",
            json=payload,
            catch_response=True,
        ) as response:
            if response.status_code == 422:
                response.success()
            else:
                response.failure(f"Expected 422, got {response.status_code}")

    @task(1)
    def check_health(self):
        """
        Periodically check health endpoint.

        Weight: 1
        Expected: 200 OK with healthy status
        """
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    response.success()
                else:
                    response.failure(f"Unhealthy: {data}")
            else:
                response.failure(f"Got status code {response.status_code}")


class HighLoadUser(HttpUser):
    """
    High-load scenario: minimal wait time between requests.

    Use this to test maximum throughput and stress conditions.
    Run with: locust --users 500 --spawn-rate 50 -H http://localhost:8000 --class-picker
    """

    wait_time = between(0.1, 0.5)

    @task
    def score_fast(self):
        """Fast scoring requests with minimal variation."""
        payload = {
            "age": 35,
            "income": 75000,
            "credit_history_years": 8,
            "existing_loans": 2,
            "debt_to_income_ratio": 0.25,
            "savings": 25000,
            "employment_status": "employed",
            "employment_years": 5,
        }
        self.client.post("/score", json=payload)
