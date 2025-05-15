# Tests

This directory contains tests for the application.
The directory/file structure should mimic the application structure.

## Example Structure

- `core/` - Tests for core functionality
  - `logging/` - Tests for the logging system
    - `test_formatters.py` - Tests for log formatters
    - `test_handlers.py` - Tests for log handlers
    - `test_logger.py` - Tests for the LoggingManager

## Running Tests

To run all tests:

```bash
pytest
```

To run tests with verbose output:

```bash
pytest -v
```

To run a specific test file:

```bash
pytest tests/core/logging/test_formatters.py
```

To run a specific test class:

```bash
pytest tests/core/logging/test_formatters.py::TestJsonFormatter
```

To run a specific test:

```bash
pytest tests/core/logging/test_formatters.py::TestJsonFormatter::test_format_output
```

## Pytest Fixtures and conftest.py

The `conftest.py` file at the root of the tests directory contains shared pytest fixtures that are automatically available to all test files without explicitly importing them.

### Available Fixtures

- `client()`: Returns a FastAPI TestClient instance for testing API endpoints without starting a server.

  ```python
  def test_read_main(client):
      response = client.get("/")
      assert response.status_code == 200
  ```

- `db_session()`: Creates an isolated in-memory SQLite database session for testing.
  ```python
  def test_create_document(db_session):
      # Create a document and add to session
      document = Document(title="Test Document")
      db_session.add(document)
      db_session.commit()

      # Query to verify
      saved_document = db_session.get(Document, document.id)
      assert saved_document.title == "Test Document"
  ```

### Adding New Fixtures

To add new fixtures, simply define them in the `conftest.py` file. They'll be automatically discovered by pytest and made available to all test files.

```python
@pytest.fixture
def sample_document():
    """Return a sample document for testing."""
    return Document(title="Sample Document", content="Test content")
```

## Coverage

To run tests with coverage reporting, install pytest-cov:

```bash
pytest --cov=src
```

For HTML coverage reports:

```bash
pytest --cov=src --cov-report=html
```

