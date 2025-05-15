import logging

from src.core.logging.formatters.base import FormatterBase


class StandardFormatter(FormatterBase):
    """Standard log formatter with configurable format string."""
    
    def __init__(self, format_str: str = None):
        """
        Initialize with optional custom format string.
        
        Args:
            format_str: Custom log format string. If None, uses default format.
        """
        self.format_str = format_str or "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    def get_formatter(self) -> logging.Formatter:
        """Return a configured logging.Formatter with the standard format."""
        return logging.Formatter(self.format_str) 