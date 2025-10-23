# AI Model Router

A production-ready REST API that intelligently routes LLM requests across multiple providers (OpenAI, Anthropic, Google Gemini, DeepSeek) with comprehensive cost tracking, automatic optimization, and real-time analytics.

## Project Goals

- Learn API development (building, testing, consuming)
- Practice Git/GitHub workflows with feature branches and PRs
- Build practical understanding of LLM provider integration
- Implement cost optimization algorithms
- Create production-ready code with testing and documentation

## Current Status

✅ **All Phases Complete!**

- **Phase 1: MVP** - Single provider routing with cost tracking
- **Phase 2: Multi-Provider Support** - 4 providers, 14 models
- **Phase 3: Dashboard** - React frontend with analytics
- **Phase 4: Cost Optimization** - Automatic cheapest model selection
- **Phase 5: Advanced Features** - A/B comparison, caching, batch processing
- **Phase 6: Production Readiness** - Docker, logging, Redis
- **Phase 7: Testing** - 49 automated tests, 50% coverage

**This is a production-ready AI model router with comprehensive observability.**

## Features

### 🚀 Core Capabilities
- **Multi-Provider Routing** - Route to OpenAI, Anthropic, Google Gemini, or DeepSeek
- **14 Models Supported** - From budget ($0.28/1M tokens) to premium ($75/1M tokens)
- **Cost Optimization** - Automatically select cheapest model for each request
- **Budget Enforcement** - Set spending limits per user
- **Comprehensive Analytics** - Track costs, latency, success rates by model/provider

### 📊 Observability
- **Real-time Dashboard** - React frontend with charts and filters
- **Request History** - View full prompts, responses, and costs
- **Cost Breakdowns** - Analyze spending by provider/model
- **Performance Metrics** - Track latency and error rates

### ⚡ Advanced Features
- **A/B Comparison** - Test multiple models simultaneously
- **Response Caching** - Redis-based caching for cost savings
- **Batch Processing** - Process multiple prompts in parallel
- **Token Estimation** - Predict costs before making requests

### 🧪 Production Ready
- **Docker Deployment** - Full stack containerization
- **Structured Logging** - JSON logs with correlation IDs
- **49 Automated Tests** - 50% code coverage with pytest
- **API Documentation** - Auto-generated OpenAPI docs

## Tech Stack

**Backend:**
- Python 3.11+ with FastAPI
- PostgreSQL for data persistence
- Redis for caching
- SQLAlchemy ORM
- Alembic for migrations
- pytest for testing

**Frontend:**
- React + TypeScript
- TailwindCSS for styling
- Recharts for visualizations
- Axios for API calls

**Infrastructure:**
- Docker & Docker Compose
- Git & GitHub for version control

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Node.js 18+ (for frontend)

### Backend Setup
```bash
# 1. Clone the repository
git clone https://github.com/kevinmcmahonxyz/ai-model-router.git
cd ai-model-router

# 2. Start PostgreSQL and Redis
docker-compose up -d

# 3. Set up backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your API keys:
# - OPENAI_API_KEY
# - ANTHROPIC_API_KEY
# - GOOGLE_API_KEY
# - DEEPSEEK_API_KEY

# 5. Run database migrations
alembic upgrade head

# 6. Seed initial data
python src/utils/seed_data.py
python src/utils/create_api_key.py

# 7. Start the server
uvicorn src.main:app --reload --port 8001
```

Visit http://127.0.0.1:8001/docs for interactive API documentation.

### Frontend Setup
```bash
# From project root
cd frontend
npm install
npm run dev
```

Visit http://localhost:5173 for the dashboard.

## API Reference

### Authentication

All endpoints require authentication via API key header:
```bash
X-API-Key: your_api_key_here
```

### Chat Completion API

#### POST /v1/chat/completions

Route a chat completion request to an LLM provider.

**Manual Mode:**
```json
{
  "messages": [
    {"role": "user", "content": "What is the capital of France?"}
  ],
  "model": "gpt-4o-mini"
}
```

**Cost-Optimized Mode:**
```json
{
  "messages": [
    {"role": "user", "content": "What is the capital of France?"}
  ],
  "mode": "cost-optimized"
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

### A/B Comparison API

#### POST /v1/chat/compare

Compare responses from multiple models simultaneously.
```json
{
  "messages": [
    {"role": "user", "content": "Explain quantum computing"}
  ],
  "models": ["gpt-4o", "claude-sonnet-4", "gemini-2.0-flash"]
}
```

### Batch Processing API

#### POST /v1/chat/batch

Process multiple prompts in parallel.
```json
{
  "requests": [
    {"messages": [{"role": "user", "content": "Hello"}]},
    {"messages": [{"role": "user", "content": "Goodbye"}]}
  ],
  "model": "gpt-4o-mini"
}
```

### Analytics API

#### GET /v1/analytics/usage

Get aggregate usage statistics and cost breakdowns.

**Query Parameters:**
- `days` (int, optional): Number of days to analyze (default: 30, max: 365)

#### GET /v1/analytics/requests

Get paginated list of requests with filtering.

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 20, max: 100)
- `model` (string): Filter by model ID
- `status` (string): Filter by status ("success" or "error")
- `search` (string): Search in prompt text
- `start_date`, `end_date` (datetime): Date range filters

#### GET /v1/analytics/requests/{request_id}

Get full details of a specific request.

#### GET /v1/analytics/models

Get list of all available models with pricing information.

### Budget API

#### GET /v1/budget

Get current budget status and spending.

#### PUT /v1/budget/limit

Set spending limit.
```json
{
  "limit_usd": 100.00
}
```

#### POST /v1/budget/reset

Reset spending for current period.

## Testing

### Prerequisites

Tests use PostgreSQL (not SQLite) to ensure 100% parity with production.

**Before running tests:**

1. **Ensure PostgreSQL is running:**
```bash
docker-compose up -d postgres
```

2. **Create test database (one-time setup):**
```bash
docker-compose exec postgres psql -U router_user -d router_db -c "CREATE DATABASE router_test_db;"
```

### Running Tests
```bash
# Activate virtual environment
cd backend
source venv/bin/activate

# Run all tests
pytest -v

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_analytics.py -v

# Run tests in parallel (faster)
pytest -n auto
```

### Test Structure
```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_analytics.py        # Analytics endpoint tests (24 tests)
├── test_integration.py      # Integration tests (8 tests)
├── test_cost_calculator.py  # Cost calculation tests (4 tests)
└── test_openai_provider.py  # Provider tests with mocking (6 tests)

scripts/manual_tests/        # Manual integration tests (preserved for development)
```

**Current Test Coverage:** 50% (49 passing tests)

## Project Structure
```
ai-model-router/
├── backend/
│   ├── src/
│   │   ├── api/              # FastAPI routes and models
│   │   ├── models/           # Database models
│   │   ├── providers/        # LLM provider integrations
│   │   ├── services/         # Business logic
│   │   └── utils/            # Utilities and scripts
│   ├── tests/                # Automated test suite
│   ├── scripts/              # Manual tests and utilities
│   ├── alembic/              # Database migrations
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   └── services/         # API client
│   └── package.json
└── docker-compose.yml        # Container orchestration
```

## Database Schema
```
users
  - id (UUID)
  - api_key (string)
  - created_at (datetime)
  - is_active (boolean)
  - spending_limit_usd (decimal)
  - current_spending_usd (decimal)

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
  - input_price_per_1m_tokens (decimal)
  - output_price_per_1m_tokens (decimal)
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
  - input_cost_usd, output_cost_usd, total_cost_usd (decimals)
  - latency_ms (integer)
  - status (string)
  - error_message (text)
  - created_at, completed_at (datetime)
```

## Development Workflow

### Running Locally
```bash
# Start services
docker-compose up -d

# Backend (terminal 1)
cd backend
source venv/bin/activate
uvicorn src.main:app --reload --port 8001

# Frontend (terminal 2)
cd frontend
npm run dev
```

### Making Changes
```bash
# 1. Create feature branch
git checkout -b feature/your-feature-name

# 2. Make changes and test
pytest -v

# 3. Commit with conventional commits
git add .
git commit -m "feat(scope): description"

# 4. Push and create PR
git push origin feature/your-feature-name
```

### Database Migrations
```bash
# Create migration after model changes
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Common Commands
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f postgres
docker-compose logs -f redis

# Run migrations
alembic upgrade head

# Seed database
python src/utils/seed_data.py

# Create API key
python src/utils/create_api_key.py

# Generate test data
python src/utils/generate_test_data.py

# Run tests with coverage
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

## Environment Variables

Create a `.env` file in the `backend/` directory:
```env
# Database
DATABASE_URL=postgresql://router_user:router_password@localhost:5433/router_db

# LLM Provider API Keys
OPENAI_API_KEY=sk-proj-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
GOOGLE_API_KEY=your-key-here
DEEPSEEK_API_KEY=your-key-here

# Redis
REDIS_URL=redis://localhost:6379

# Application
APP_ENV=development
LOG_LEVEL=INFO
```

## Supported Models

### OpenAI
- `gpt-4o` - $2.50/$10.00 per 1M tokens
- `gpt-4o-mini` - $0.15/$0.60 per 1M tokens
- `gpt-3.5-turbo` - $0.50/$1.50 per 1M tokens

### Anthropic
- `claude-opus-4.1` - $15.00/$75.00 per 1M tokens
- `claude-opus-4` - $15.00/$75.00 per 1M tokens
- `claude-sonnet-4.5` - $3.00/$15.00 per 1M tokens
- `claude-sonnet-4` - $3.00/$15.00 per 1M tokens
- `claude-haiku-3.5` - $0.80/$4.00 per 1M tokens

### DeepSeek
- `deepseek-chat` - $0.14/$0.28 per 1M tokens (cheapest!)

### Google Gemini
- `gemini-2.0-flash` - $0.10/$0.40 per 1M tokens
- `gemini-2.5-flash` - $0.075/$0.30 per 1M tokens
- `gemini-2.5-flash-lite` - $0.0375/$0.15 per 1M tokens
- `gemini-2.5-pro` - $1.25/$5.00 per 1M tokens

## Troubleshooting

### Port Conflicts
- PostgreSQL runs on port 5433 (not default 5432)
- Backend API runs on port 8001 (not default 8000)
- Frontend runs on port 5173
- Redis runs on port 6379

### Database Issues
```bash
# Check if postgres is running
docker-compose ps

# View logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres

# Reset database (WARNING: destroys all data)
docker-compose exec postgres psql -U router_user -d router_db \
  -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
alembic upgrade head
```

### Redis Issues
```bash
# Check Redis
docker-compose logs redis

# Test Redis connection
docker-compose exec redis redis-cli ping
```

### Migration Issues
```bash
# View migration history
alembic history

# Check current version
alembic current

# Manually stamp version
alembic stamp head
```

## Project Phases

- ✅ **Phase 1: MVP** - Single provider routing with cost tracking
- ✅ **Phase 2: Multi-Provider Support** - Add Anthropic, Google, DeepSeek
- ✅ **Phase 3: Dashboard** - React UI with analytics
- ✅ **Phase 4: Cost Optimization** - Automatic cheapest-model selection
- ✅ **Phase 5: Advanced Features** - A/B testing, caching, batch processing
- ✅ **Phase 6: Production Readiness** - Docker, logging, configuration
- ✅ **Phase 7: Testing** - Comprehensive test suite

## License

MIT

## Contact

- GitHub: [@kevinmcmahonxyz](https://github.com/kevinmcmahonxyz)
- Project: [ai-model-router](https://github.com/kevinmcmahonxyz/ai-model-router)