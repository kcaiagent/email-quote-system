# Test Suite

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run specific test
pytest tests/test_auth.py::test_api_key_required_for_business_creation

# Run with verbose output
pytest -v
```

## Test Structure

- `conftest.py`: Pytest fixtures (database, client, etc.)
- `test_health.py`: Health check endpoint tests
- `test_auth.py`: API authentication tests
- `test_wix_endpoints.py`: Wix integration endpoint tests
- `test_business_endpoints.py`: Business management endpoint tests

## Adding New Tests

1. Create a new file `test_*.py` in the `tests/` directory
2. Import fixtures from `conftest.py` as needed
3. Use `client` fixture for API testing
4. Use `db_session` fixture for database operations

## Example Test

```python
def test_example(client, headers):
    response = client.get("/api/endpoint", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "expected_field" in data
```



