import logging
from typing import Dict

from src.core.config.settings import settings
from src.core.logging.handlers.base import HandlerBase


class LoggingManager:
    """
    Manager for configuring and managing application logging.
    
    This class provides a centralized interface for configuring application 
    logging with multiple handlers and formatters.
    """
    
    def __init__(self, default_level: str = None):
        """
        Initialize the logging manager.
        
        Args:
            default_level: Default log level. If None, uses settings.LOG_LEVEL.
        """
        self.default_level = default_level or settings.LOG_LEVEL
        self.handlers: Dict[str, HandlerBase] = {}
        self.is_configured = False
    
    def add_handler(self, name: str, handler: HandlerBase) -> "LoggingManager":
        """
        Add a handler to the logging configuration.
        
        Args:
            name: A unique name for this handler
            handler: The handler instance to add
            
        Returns:
            Self for method chaining
        
        Raises:
            ValueError: If a handler with the same name already exists
        """
        if name in self.handlers:
            raise ValueError(f"Handler with name '{name}' already exists")

        if not isinstance(handler, HandlerBase):
            raise ValueError("Handler must be an instance of HandlerBase")
        
        self.handlers[name] = handler
        return self
    
    def remove_handler(self, name: str) -> "LoggingManager":
        """
        Remove a handler from the logging configuration.
        
        Args:
            name: The name of the handler to remove
            
        Returns:
            Self for method chaining
            
        Raises:
            KeyError: If no handler with the given name exists
        """
        if name not in self.handlers:
            raise KeyError(f"No handler with name '{name}' exists")
        
        del self.handlers[name]
        return self
    
    def configure(self, clear_existing_handlers: bool = True) -> None:
        """
        Configure the root logger with all registered handlers.
        
        Args:
            clear_existing_handlers: Whether to clear existing handlers from the root logger
        """
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.default_level))
        
        # Clear existing handlers if requested
        if clear_existing_handlers and root_logger.handlers:
            root_logger.handlers.clear()
        
        # Add all registered handlers
        for handler in self.handlers.values():
            root_logger.addHandler(handler.get_handler())
        
        self.is_configured = True
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger instance for a specific module.
        
        Args:
            name: Name of the module requesting a logger
            
        Returns:
            A configured logger instance
        """
        if not self.is_configured:
            self.configure()
        
        return logging.getLogger(name)
