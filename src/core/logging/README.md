# Logging System

The logging system is designed to be modular, extensible, and configuration-driven. This document explains how to use the logging system, configure it for different environments, and extend it with custom components.

## Architecture

The logging system consists of several key components:

- **LoggingManager**: Central manager for configuring and managing application-wide logging
- **Handlers**: Process log records and direct them to appropriate outputs (console, file, etc.)
- **Formatters**: Define how log messages are formatted before being emitted

## Basic Usage

### Setting Up Logging

```python
from src.core.logging.logger import LoggingManager
from src.core.logging.handlers.console import ConsoleHandler

# Create a logging manager
logging_manager = LoggingManager()

# Add handlers
logging_manager.add_handler("console", ConsoleHandler())

# Configure logging
logging_manager.configure()

# Get a logger for a specific module
logger = logging_manager.get_logger(__name__)

# Use the logger
logger.info("Application started")
logger.error("An error occurred", exc_info=True)
```

### Environment-Based Configuration

The default log level is determined by the application settings:

```python
# In development: DEBUG level
# In production: INFO level
from src.core.config.settings import settings

# settings.LOG_LEVEL will be "DEBUG" in development and "INFO" in production
```

## Advanced Usage

### Multiple Handlers

You can add multiple handlers to direct logs to different outputs:

```python
from src.core.logging.logger import LoggingManager
from src.core.logging.handlers.console import ConsoleHandler
from src.core.logging.handlers.file import FileHandler
from src.core.logging.formatters.json import JSONFormatter

# Create logging manager
logging_manager = LoggingManager()

# Add console handler with default formatting
logging_manager.add_handler("console", ConsoleHandler())

# Add file handler with JSON formatting
file_handler = FileHandler("app.log")
file_handler.set_formatter(JSONFormatter())
logging_manager.add_handler("file", file_handler)

# Configure logging
logging_manager.configure()
```

### Contextual Logging

```python
# Get a logger for your module
logger = logging_manager.get_logger(__name__)

# Add context to logs
logger.info("User authentication", extra={"user_id": "12345", "ip": "192.168.1.1"})
```

## Extending the Logging System

### Creating a Custom Handler

1. Create a new file in the `handlers` directory
2. Extend the `HandlerBase` class
3. Implement the required methods

Example:

```python
# src/core/logging/handlers/custom_handler.py
import logging
from src.core.logging.handlers.base import HandlerBase

class CustomHandler(HandlerBase):
    def __init__(self, level=None):
        super().__init__(level)
        # Custom initialization

    def get_handler(self) -> logging.Handler:
        # Create and return your custom handler
        handler = logging.Handler()  # Replace with your actual handler
        self._configure_handler(handler)
        return handler
```

### Creating a Custom Formatter

1. Create a new file in the `formatters` directory
2. Extend the `FormatterBase` class
3. Implement the required methods

Example:

```python
# src/core/logging/formatters/custom_formatter.py
import logging
from src.core.logging.formatters.base import FormatterBase

class CustomFormatter(FormatterBase):
    def get_formatter(self) -> logging.Formatter:
        # Create and return your custom formatter
        return logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
```

## Best Practices

1. **Use named loggers**: Always use `__name__` as the logger name to create a hierarchy based on the module structure.
2. **Add context**: Use the `extra` parameter to add contextual information to logs.
3. **Environment-specific configuration**: Use different handlers and log levels for development vs. production.
4. **Test all components**: Ensure each formatter and handler has proper unit tests.
5. **Structure logs**: Consider using structured logging (e.g., JSON) for machine readability.

