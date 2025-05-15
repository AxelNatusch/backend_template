import json
import logging

from src.core.logging.formatters import JsonFormatter, StandardFormatter


def create_log_record(message="Test message", level=logging.INFO, name="test_logger"):
    """Helper function to create a log record for testing."""
    record = logging.LogRecord(
        name=name,
        level=level,
        pathname="test_file.py",
        lineno=42,
        msg=message,
        args=(),
        exc_info=None,
    )
    return record


class TestStandardFormatter:
    """Tests for the StandardFormatter class."""

    def test_get_formatter(self):
        """Test that get_formatter returns a Formatter instance."""
        formatter = StandardFormatter().get_formatter()
        assert isinstance(formatter, logging.Formatter)

    def test_format_output(self):
        """Test that the formatter produces the expected output format."""
        formatter = StandardFormatter().get_formatter()
        record = create_log_record()
        formatted_message = formatter.format(record)

        # Basic assertions about the formatted message
        assert record.name in formatted_message
        assert record.levelname in formatted_message
        assert record.getMessage() in formatted_message


class TestJsonFormatter:
    """Tests for the JsonFormatter class."""

    def test_get_formatter(self):
        """Test that get_formatter returns a Formatter instance."""
        formatter = JsonFormatter().get_formatter()
        assert isinstance(formatter, logging.Formatter)

    def test_format_output(self):
        """Test that the formatter produces valid JSON."""
        formatter = JsonFormatter().get_formatter()
        record = create_log_record()
        formatted_message = formatter.format(record)

        # Verify it's valid JSON
        log_data = json.loads(formatted_message)

        # Check required fields
        assert log_data["logger"] == record.name
        assert log_data["level"] == record.levelname
        assert log_data["message"] == record.getMessage()
        assert "timestamp" in log_data
        assert "location" in log_data
        assert log_data["location"]["file"] == record.pathname
        assert log_data["location"]["line"] == record.lineno
        assert log_data["location"]["function"] == record.funcName

    def test_additional_fields(self):
        """Test that additional_fields are included in the output."""
        additional_fields = {"app_name": "backend_template", "environment": "test"}
        formatter = JsonFormatter(additional_fields=additional_fields).get_formatter()
        record = create_log_record()
        formatted_message = formatter.format(record)

        log_data = json.loads(formatted_message)

        # Check that additional fields are present
        for key, value in additional_fields.items():
            assert log_data[key] == value

    def test_extra_attributes(self):
        """Test that extra attributes from the log record are included in the output."""
        formatter = JsonFormatter().get_formatter()
        record = create_log_record()

        # Add extra attributes to the record
        extra_data = {
            "user_id": "12345",
            "request_id": "abc-123",
            "client_ip": "127.0.0.1",
        }
        record.extra = extra_data

        formatted_message = formatter.format(record)
        log_data = json.loads(formatted_message)

        # Check that extra attributes are present in the output
        for key, value in extra_data.items():
            assert log_data[key] == value

    def test_timestamp_format(self):
        """Test that timestamp formatting works correctly."""
        custom_format = "%Y/%m/%d-%H:%M"
        formatter = JsonFormatter(timestamp_format=custom_format).get_formatter()
        record = create_log_record()
        formatted_message = formatter.format(record)

        log_data = json.loads(formatted_message)

        # Check timestamp format (we can't check exact value easily)
        assert "timestamp" in log_data
        # Basic format validation - should contain / and :
        assert "/" in log_data["timestamp"]
        assert ":" in log_data["timestamp"]

    def test_no_timestamp(self):
        """Test that timestamp can be disabled."""
        formatter = JsonFormatter(include_timestamp=False).get_formatter()
        record = create_log_record()
        formatted_message = formatter.format(record)

        log_data = json.loads(formatted_message)

        # Check timestamp is not included
        assert "timestamp" not in log_data

