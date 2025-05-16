import logging
from abc import ABC, abstractmethod


class FormatterBase(ABC):
    """Abstract base class for log formatters."""

    @abstractmethod
    def get_formatter(self) -> logging.Formatter:
        """Return a configured logging.Formatter instance."""
        pass
