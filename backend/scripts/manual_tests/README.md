# Manual Integration Tests

These are manual test scripts used during development. Unlike the automated tests in `tests/`, these:

- Require a running server (`uvicorn src.main:app --reload --port 8001`)
- Make real API calls to test end-to-end workflows  
- Are useful for debugging and demonstrations

## Usage
```bash
# 1. Start the server
cd backend
source venv/bin/activate
uvicorn src.main:app --reload --port 8001

# 2. In another terminal, run a manual test
cd backend
source venv/bin/activate
python scripts/manual_tests/test_cost_optimized_api.py
```

For automated testing, use `pytest` in the `tests/` directory instead.