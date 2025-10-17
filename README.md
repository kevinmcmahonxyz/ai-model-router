# AI Model Router

A REST API that routes LLM requests to multiple providers with comprehensive cost tracking and observability.

## Project Goals

- Learn API development (building, testing, consuming)
- Practice Git/GitHub workflows
- Build practical understanding of LLM provider integration

## Current Status

**Phase 1: MVP** - ✅ Complete
**Phase 3: Dashboard Backend APIs** - ✅ Complete

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL (via Docker)

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/kevinmcmahonxyz/ai-model-router.git
cd ai-model-router

# 2. Start PostgreSQL
docker-compose up -d postgres

# 3. Set up backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 5. Run database migrations
alembic upgrade head

# 6. Seed initial data
python src/utils/seed_data.py
python src/utils/create_api_key.py

# 7. Start the server
uvicorn src.main:app --reload --port 8001
```

Visit http://127.0.0.1:8001/docs for interactive API documentation.

## API Reference

### Authentication

All endpoints require authentication via API key header:

```bash
X-API-Key: your_api_key_here
```

### Chat Completion API

#### POST /v1/chat/completions

Route a chat completion request to an LLM provider.

**Request:**
```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is the capital of France?"}
  ],
  "model": "gpt-4o-mini",
  "temperature": 0.7,
  "max_tokens": 500
}
```

**Response:**
```json
{
  "id": "req_abc123",
  "model": "gpt-4o-mini",
  "provider": "openai",
  "content": "The capital of France is Paris.",
  "finish_reason": "stop",
  "usage": {
    "prompt_tokens": 23,
    "completion_tokens": 8,
    "total_tokens": 31,
    "input_cost_usd": 0.00000345,
    "output_cost_usd": 0.00000480,
    "total_cost_usd": 0.00000825
  },
  "latency_ms": 1234,
  "created_at": "2025-10-16T10:30:00Z"
}
```

**Example:**
```bash
curl -X POST "http://127.0.0.1:8001/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}],
    "model": "gpt-4o-mini"
  }'
```

---

### Analytics API

#### GET /v1/analytics/usage

Get aggregate usage statistics and cost breakdowns.

**Query Parameters:**
- `days` (int, optional): Number of days to analyze (default: 30, max: 365)

**Response:**
```json
{
  "total_requests": 145,
  "total_cost_usd": 0.234567,
  "avg_latency_ms": 1234,
  "success_rate": 0.98,
  "by_provider": [
    {
      "provider": "openai",
      "requests": 145,
      "cost_usd": 0.234567
    }
  ],
  "by_model": [
    {
      "model": "gpt-4o-mini",
      "requests": 100,
      "cost_usd": 0.150000
    },
    {
      "model": "gpt-4o",
      "requests": 45,
      "cost_usd": 0.084567
    }
  ],
  "daily_stats": [
    {
      "date": "2025-10-15",
      "requests": 20,
      "cost_usd": 0.045123
    }
  ]
}
```

**Example:**
```bash
curl -X GET "http://127.0.0.1:8001/v1/analytics/usage?days=7" \
  -H "X-API-Key: $API_KEY"
```

---

#### GET /v1/analytics/requests

Get paginated list of requests with filtering and search.

**Query Parameters:**
- `page` (int, optional): Page number (default: 1, min: 1)
- `per_page` (int, optional): Items per page (default: 20, max: 100)
- `model` (string, optional): Filter by model ID (e.g., "gpt-4o-mini")
- `status` (string, optional): Filter by status ("success" or "error")
- `search` (string, optional): Search in prompt text
- `start_date` (datetime, optional): Filter by start date (ISO format)
- `end_date` (datetime, optional): Filter by end date (ISO format)

**Response:**
```json
{
  "requests": [
    {
      "id": "abc-123",
      "created_at": "2025-10-16T10:30:00Z",
      "model": "gpt-4o-mini",
      "provider": "openai",
      "prompt_preview": "What is the capital of France?",
      "input_tokens": 23,
      "output_tokens": 8,
      "total_cost_usd": 0.00000825,
      "latency_ms": 1234,
      "status": "success"
    }
  ],
  "total": 145,
  "page": 1,
  "per_page": 20,
  "total_pages": 8
}
```

**Examples:**
```bash
# Get first page
curl -X GET "http://127.0.0.1:8001/v1/analytics/requests" \
  -H "X-API-Key: $API_KEY"

# Filter by model
curl -X GET "http://127.0.0.1:8001/v1/analytics/requests?model=gpt-4o-mini" \
  -H "X-API-Key: $API_KEY"

# Search and filter
curl -X GET "http://127.0.0.1:8001/v1/analytics/requests?search=weather&status=success" \
  -H "X-API-Key: $API_KEY"

# Date range
curl -X GET "http://127.0.0.1:8001/v1/analytics/requests?start_date=2025-10-01T00:00:00Z&end_date=2025-10-15T23:59:59Z" \
  -H "X-API-Key: $API_KEY"
```

---

#### GET /v1/analytics/requests/{request_id}

Get full details of a specific request.

**Path Parameters:**
- `request_id` (string): UUID of the request

**Response:**
```json
{
  "id": "abc-123",
  "created_at": "2025-10-16T10:30:00Z",
  "completed_at": "2025-10-16T10:30:02Z",
  "model": "gpt-4o-mini",
  "provider": "openai",
  "prompt_text": "What is the capital of France?",
  "response_text": "The capital of France is Paris.",
  "input_tokens": 23,
  "output_tokens": 8,
  "total_tokens": 31,
  "input_cost_usd": 0.00000345,
  "output_cost_usd": 0.00000480,
  "total_cost_usd": 0.00000825,
  "latency_ms": 1234,
  "status": "success",
  "error_message": null
}
```

**Example:**
```bash
curl -X GET "http://127.0.0.1:8001/v1/analytics/requests/abc-123" \
  -H "X-API-Key: $API_KEY"
```

---

#### GET /v1/analytics/models

Get list of all available models with pricing information.

**Response:**
```json
[
  {
    "id": 1,
    "model_id": "gpt-4o-mini",
    "display_name": "GPT-4o Mini",
    "provider": "openai",
    "input_price_per_1m_tokens": 0.15,
    "output_price_per_1m_tokens": 0.60,
    "context_window": 128000,
    "is_active": true
  },
  {
    "id": 2,
    "model_id": "gpt-4o",
    "display_name": "GPT-4o",
    "provider": "openai",
    "input_price_per_1m_tokens": 2.50,
    "output_price_per_1m_tokens": 10.00,
    "context_window": 128000,
    "is_active": true
  }
]
```

**Example:**
```bash
curl -X GET "http://127.0.0.1:8001/v1/analytics/models" \
  -H "X-API-Key: $API_KEY"
```

---

## Testing

### **Prerequisites**

Tests use PostgreSQL (not SQLite) to ensure 100% parity with production. This catches database-specific issues like UUID handling.

**Before running tests:**

1. **Ensure PostgreSQL is running:**
```bash
docker-compose up -d postgres
```

2. **Create test database (one-time setup):**
```bash
docker-compose exec postgres psql -U router_user -d router_db -c "CREATE DATABASE router_test_db;"
```

That's it! The test suite will automatically create/drop tables as needed.

### **Running Tests**

```bash
# Activate virtual environment
cd backend
source venv/bin/activate

# Run all tests
pytest -v

# Run specific test file
pytest tests/test_analytics.py -v
pytest tests/test_integration.py -v

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html

# Run tests in parallel (faster)
pytest -n auto
```

### **Test Structure**

```
tests/
├── conftest.py           # Shared fixtures and test configuration
├── test_analytics.py     # Unit tests for analytics endpoints (24 tests)
└── test_integration.py   # Integration tests for workflows (8 tests)
```

### **Why PostgreSQL for Tests?**

We use PostgreSQL instead of SQLite because:
- ✅ **100% production parity** - catches DB-specific bugs before production
- ✅ **UUID support** - SQLite doesn't natively support UUID types
- ✅ **Accurate behavior** - same query behavior as production
- ✅ **Industry standard** - recommended by Django, Rails, and testing best practices

The slight overhead is worth the confidence that tests match production behavior.

### **Troubleshooting Tests**

**"Connection refused" errors:**
```bash
# Make sure PostgreSQL is running
docker-compose ps

# Restart if needed
docker-compose restart postgres
```

**"Database does not exist" error:**
```bash
# Recreate test database
docker-compose exec postgres psql -U router_user -d router_db -c "DROP DATABASE IF EXISTS router_test_db;"
docker-compose exec postgres psql -U router_user -d router_db -c "CREATE DATABASE router_test_db;"
```

**Tests are slow:**
```bash
# Run in parallel (requires pytest-xdist)
pip install pytest-xdist
pytest -n auto
```

## Development Workflow

### Running Tests Before Commit

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Run tests
pytest -v

# 3. Check code works
uvicorn src.main:app --reload --port 8001
# Test manually or with curl
```

### Git Workflow

```bash
# 1. Create feature branch
git checkout -b feature/your-feature

# 2. Make changes and commit
git add .
git commit -m "feat: your feature description"

# 3. Push and create PR
git push origin feature/your-feature
```

## Tech Stack

**Backend:**
- Python 3.11+
- FastAPI - Web framework
- SQLAlchemy - ORM
- PostgreSQL - Database
- Alembic - Database migrations
- pytest - Testing
- httpx - HTTP client

**Infrastructure:**
- Docker & Docker Compose
- Git & GitHub

## Database Schema

```
users
  - id (UUID)
  - api_key (string)
  - created_at (datetime)
  - is_active (boolean)

providers
  - id (integer)
  - name (string)
  - base_url (string)
  - is_active (boolean)

models
  - id (integer)
  - provider_id (foreign key)
  - model_id (string)
  - display_name (string)
  - input_price_per_1m_tokens (float)
  - output_price_per_1m_tokens (float)
  - context_window (integer)
  - is_active (boolean)

requests
  - id (UUID)
  - user_id (foreign key)
  - model_id (foreign key)
  - provider_id (foreign key)
  - prompt_text (text)
  - response_text (text)
  - input_tokens, output_tokens, total_tokens (integers)
  - input_cost_usd, output_cost_usd, total_cost_usd (floats)
  - latency_ms (integer)
  - status (string)
  - error_message (text)
  - created_at, completed_at (datetime)
```

## Project Phases

- [x] **Phase 1: MVP** - Single provider routing with cost tracking
- [ ] **Phase 2: Multi-Provider Support** - Add Anthropic, Google, DeepSeek
- [x] **Phase 3: Dashboard (Backend)** - Analytics API endpoints ← **Currently Here**
- [ ] **Phase 3: Dashboard (Frontend)** - React UI
- [ ] **Phase 4: Cost Optimization** - Automatic cheapest-model selection
- [ ] **Phase 5: Advanced Features** - A/B testing, caching, webhooks

## Common Commands

```bash
# Start database
docker-compose up -d postgres

# Start backend (from backend/)
source venv/bin/activate
uvicorn src.main:app --reload --port 8001

# Run migrations
alembic upgrade head

# Create migration
alembic revision --autogenerate -m "description"

# Seed database
python src/utils/seed_data.py

# Create API key
python src/utils/create_api_key.py

# Generate test data
python src/utils/generate_test_data.py

# Run tests
pytest -v

# Check database
docker-compose exec postgres psql -U router_user -d router_db
```

## Environment Variables

Create a `.env` file in the `backend/` directory:

```env
DATABASE_URL=postgresql://router_user:router_password@localhost:5433/router_db
OPENAI_API_KEY=sk-proj-your-key-here
APP_ENV=development
LOG_LEVEL=INFO
```

## Troubleshooting

**Port conflicts:**
- PostgreSQL runs on port 5433 (not default 5432)
- Backend API runs on port 8001 (not default 8000)

**Database connection issues:**
```bash
# Check if postgres is running
docker-compose ps

# View logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

**Migration issues:**
```bash
# Reset database (WARNING: destroys all data)
docker-compose exec postgres psql -U router_user -d router_db \
  -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Rerun migrations
alembic upgrade head
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure tests pass: `pytest -v`
5. Commit with conventional commits
6. Push and create a pull request

## License

MIT

## Contact

- GitHub: [@kevinmcmahonxyz](https://github.com/kevinmcmahonxyz)
- Project: [ai-model-router](https://github.com/kevinmcmahonxyz/ai-model-router)