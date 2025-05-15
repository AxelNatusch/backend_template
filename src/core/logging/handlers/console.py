import logging
import sys

from src.core.logging.formatters.base import FormatterBase
from src.core.logging.handlers.base import HandlerBase


class ConsoleHandler(HandlerBase):
    """Handler that outputs logs to the console."""
    
    def __init__(
        self, 
        formatter: FormatterBase = None, 
        level: str = None,
        stream=sys.stdout
    ):
        """
        Initialize a console handler.
        
        Args:
            formatter: The formatter to use
            level: The log level for this handler
            stream: The stream to output to (default: sys.stdout)
        """
        super().__init__(formatter, level)
        self.stream = stream
    
    def get_handler(self) -> logging.Handler:
        """
        Return a configured console handler.
        
        Returns:
            A configured StreamHandler
        """
        handler = logging.StreamHandler(self.stream)
        return self.configure_handler(handler) 