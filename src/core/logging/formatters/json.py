import json
import logging
import datetime
from typing import Dict, Any

from src.core.logging.formatters.base import FormatterBase


class JsonFormatter(FormatterBase):
    """
    Formatter that outputs log records as JSON objects.
    
    This formatter produces structured JSON logs with configurable
    fields and formatting options.
    """
    
    def __init__(
        self,
        include_timestamp: bool = True,
        timestamp_format: str = "%Y-%m-%d %H:%M:%S",
        additional_fields: Dict[str, Any] = None
    ):
        """
        Initialize the JSON formatter.
        
        Args:
            include_timestamp: Whether to include a formatted timestamp field
            timestamp_format: Format string for the timestamp
            additional_fields: Static fields to include in every log record
        """
        self.include_timestamp = include_timestamp
        self.timestamp_format = timestamp_format
        self.additional_fields = additional_fields or {}
        
    def get_formatter(self) -> logging.Formatter:
        """
        Return a configured logging.Formatter instance that outputs JSON.
        
        Returns:
            A logging.Formatter that formats records as JSON
        """
        return _JsonLogFormatter(
            include_timestamp=self.include_timestamp,
            timestamp_format=self.timestamp_format,
            additional_fields=self.additional_fields
        )


class _JsonLogFormatter(logging.Formatter):
    """
    Internal formatter class that converts log records to JSON.
    """
    
    def __init__(
        self,
        include_timestamp: bool = True,
        timestamp_format: str = "%Y-%m-%d %H:%M:%S",
        additional_fields: Dict[str, Any] = None
    ):
        super().__init__()
        self.include_timestamp = include_timestamp
        self.timestamp_format = timestamp_format
        self.additional_fields = additional_fields or {}
        
    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record as a JSON string.
        
        Args:
            record: The log record to format
            
        Returns:
            JSON string representation of the log record
        """
        log_data = {
            "logger": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        
        # Add timestamp if requested
        if self.include_timestamp:
            log_data["timestamp"] = datetime.datetime.fromtimestamp(
                record.created
            ).strftime(self.timestamp_format)
        
        # Add location info
        log_data["location"] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add any additional fields
        log_data.update(self.additional_fields)
        
        # Add any extra attributes from the record
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_data.update(record.extra)
        
        # Collect any non-standard attributes added via 'extra' parameter
        # Standard attributes that should be excluded from the output
        standard_attrs = {
            'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
            'funcName', 'id', 'levelname', 'levelno', 'lineno', 'module',
            'msecs', 'message', 'msg', 'name', 'pathname', 'process',
            'processName', 'relativeCreated', 'stack_info', 'thread', 'threadName', "taskName"
        }
        
        # Add any custom attributes that were added via the extra parameter
        for key, value in record.__dict__.items():
            if key not in standard_attrs and not key.startswith('_'):
                log_data[key] = value
        
        return json.dumps(log_data) 