import logging
from abc import ABC, abstractmethod

from src.core.logging.formatters.base import FormatterBase


class HandlerBase(ABC):
    """Abstract base class for log handlers."""

    def __init__(self, formatter: FormatterBase = None, level: str = None):
        """
        Initialize the handler with formatter and log level.

        Args:
            formatter: The formatter to use with this handler
            level: The log level for this handler (default: None = use root logger level)
        """
        self.formatter = formatter
        self.level = level

    @abstractmethod
    def get_handler(self) -> logging.Handler:
        """Return a configured logging.Handler instance."""
        pass

    def configure_handler(self, handler: logging.Handler) -> logging.Handler:
        """
        Apply common configuration to a handler.

        Args:
            handler: The handler to configure

        Returns:
            The configured handler
        """
        if self.formatter:
            handler.setFormatter(self.formatter.get_formatter())

        if self.level:
            handler.setLevel(getattr(logging, self.level))

        return handler
