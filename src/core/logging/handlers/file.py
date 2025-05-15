import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from src.core.logging.formatters.base import FormatterBase
from src.core.logging.handlers.base import HandlerBase


class FileHandler(HandlerBase):
    """Handler that outputs logs to a file with rotation."""
    
    def __init__(
        self,
        filepath: str,
        formatter: FormatterBase = None,
        level: str = None,
        max_bytes: int = 10 * 1024 * 1024,  # 10 MB
        backup_count: int = 5
    ):
        """
        Initialize a file handler with rotation.
        
        Args:
            filepath: Path to the log file
            formatter: The formatter to use
            level: The log level for this handler
            max_bytes: Maximum file size before rotation
            backup_count: Number of backup files to keep
        """
        super().__init__(formatter, level)
        self.filepath = filepath
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        
        # Ensure the log directory exists
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    def get_handler(self) -> logging.Handler:
        """
        Return a configured file handler with rotation.
        
        Returns:
            A configured RotatingFileHandler
        """
        handler = RotatingFileHandler(
            self.filepath,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count
        )
        return self.configure_handler(handler) 