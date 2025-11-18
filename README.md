# Scoring API

A FastAPI-based credit scoring service that evaluates applicants based on their financial profile and returns a credit score with approval decision.

## Features

- RESTful API endpoint for credit scoring
- Pydantic validation for request/response models
- Comprehensive test suite with pytest
- Docker support for containerization
- Environment-based configuration
- Structured logging

## Project Structure

```
scoring-api/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application entry point
│   ├── api.py           # API endpoints and scoring logic
│   ├── schemas.py       # Pydantic models
│   └── core/
│       ├── __init__.py
│       └── config.py    # Configuration settings
├── tests/
│   ├── __init__.py
│   └── test_api.py      # API tests
├── Dockerfile
├── .dockerignore
├── pyproject.toml
└── README.md
```

## Installation

### Using uv (recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver.

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv pip install -e .

# Install development dependencies
uv pip install -e ".[dev]"
```

### Using pip with virtual environment

```bash
# Create and activate virtual environment
python3.13 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

## Usage

### Running the API

```bash
# Using Python directly
python -m app.main

# Using uvicorn
uvicorn app.main:app --reload

# The API will be available at http://localhost:8000
```

### API Endpoints

#### Root endpoint

Get API information:

```bash
curl http://localhost:8000/
```

Response:
```json
{
  "name": "Scoring API",
  "version": "0.1.0",
  "status": "running"
}
```

#### Health check

Check API health status:

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy"
}
```

#### Score applicant

Score a credit applicant based on their financial profile.

**Example 1: Strong applicant (Approved)**

```bash
curl -X POST http://localhost:8000/score \
  -H "Content-Type: application/json" \
  -d '{
    "age": 35,
    "income": 75000,
    "credit_history_years": 8,
    "existing_loans": 2,
    "debt_to_income_ratio": 0.25,
    "savings": 25000,
    "employment_status": "employed",
    "employment_years": 5
  }'
```

Response:
```json
{
  "score": 720,
  "decision": "approved",
  "reason": "Strong financial profile with score 720. Good income level. Healthy debt-to-income ratio. Solid credit history.",
  "risk_level": "low"
}
```

**Example 2: High-income applicant (Approved)**

```bash
curl -X POST http://localhost:8000/score \
  -H "Content-Type: application/json" \
  -d '{
    "age": 42,
    "income": 120000,
    "credit_history_years": 12,
    "existing_loans": 1,
    "debt_to_income_ratio": 0.15,
    "savings": 60000,
    "employment_status": "employed",
    "employment_years": 8
  }'
```

**Example 3: Moderate applicant (Review required)**

```bash
curl -X POST http://localhost:8000/score \
  -H "Content-Type: application/json" \
  -d '{
    "age": 28,
    "income": 45000,
    "credit_history_years": 2,
    "existing_loans": 3,
    "debt_to_income_ratio": 0.4,
    "savings": 5000,
    "employment_status": "employed",
    "employment_years": 2
  }'
```

Response:
```json
{
  "score": 580,
  "decision": "review",
  "reason": "Moderate score of 580 requires manual review. Consider reducing debt-to-income ratio. Limited credit history.",
  "risk_level": "medium"
}
```

**Example 4: Weak applicant (Rejected)**

```bash
curl -X POST http://localhost:8000/score \
  -H "Content-Type: application/json" \
  -d '{
    "age": 22,
    "income": 25000,
    "credit_history_years": 0,
    "existing_loans": 5,
    "debt_to_income_ratio": 0.75,
    "savings": 500,
    "employment_status": "unemployed",
    "employment_years": 0
  }'
```

Response:
```json
{
  "score": 370,
  "decision": "rejected",
  "reason": "Low score of 370. High debt-to-income ratio. Unemployment concerns. Insufficient credit history.",
  "risk_level": "high"
}
```

**Example 5: Self-employed applicant**

```bash
curl -X POST http://localhost:8000/score \
  -H "Content-Type: application/json" \
  -d '{
    "age": 38,
    "income": 85000,
    "credit_history_years": 6,
    "existing_loans": 1,
    "debt_to_income_ratio": 0.3,
    "savings": 30000,
    "employment_status": "self_employed",
    "employment_years": 6
  }'
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api.py

# Run with verbose output
pytest -v
```

### Docker

```bash
# Build image
docker build -t scoring-api .

# Run container
docker run -p 8000:8000 scoring-api

# Run with environment variables
docker run -p 8000:8000 -e DEBUG=true scoring-api
```

## Configuration

Configuration is managed through environment variables. Create a `.env` file in the project root:

```env
# Application settings
APP_NAME=Scoring API
APP_VERSION=0.1.0
DEBUG=false

# API settings
API_PREFIX=

# Scoring thresholds
MIN_SCORE=300
MAX_SCORE=850
APPROVAL_THRESHOLD=650

# Server settings
HOST=0.0.0.0
PORT=8000
```

## API Documentation

FastAPI automatically generates interactive API documentation:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development

### Code formatting and linting

```bash
# Format code with ruff
ruff format .

# Lint code
ruff check .

# Auto-fix issues
ruff check --fix .
```

### Running in development mode

```bash
# With auto-reload
uvicorn app.main:app --reload --log-level debug
```

## Scoring Logic

The scoring algorithm evaluates applicants based on:

- **Age**: Optimal range 25-55 years
- **Income**: Higher income increases score
- **Credit History**: Longer history is better (10+ years optimal)
- **Debt-to-Income Ratio**: Lower is better (≤0.35 optimal)
- **Savings**: Higher savings increase score
- **Employment**: Stable employment with 3+ years tenure
- **Existing Loans**: Penalty for multiple loans

**Score Ranges:**
- 650-850: Approved (Low risk)
- 550-649: Review required (Medium risk)
- 300-549: Rejected (High risk)

## License

This is a demonstration project for learning FastAPI.
