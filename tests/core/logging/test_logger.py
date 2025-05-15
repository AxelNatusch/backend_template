import logging
import pytest
from unittest.mock import MagicMock, patch

from src.core.logging.logger import LoggingManager
from src.core.logging.handlers.base import HandlerBase


class MockHandler(HandlerBase):
    """Mock handler for testing."""
    
    def get_handler(self) -> logging.Handler:
        """Return a mock handler for testing."""
        return MagicMock(spec=logging.Handler)


class TestLoggingManager:
    """Tests for the LoggingManager class."""
    
    def test_init(self):
        """Test initialization with default and custom values."""
        # Default initialization
        manager = LoggingManager()
        assert manager.default_level == "DEBUG" or manager.default_level == "INFO"
        assert not manager.handlers
        assert not manager.is_configured
        
        # Custom level
        custom_level = "WARNING"
        manager = LoggingManager(default_level=custom_level)
        assert manager.default_level == custom_level
    
    def test_add_handler(self):
        """Test adding handlers."""
        manager = LoggingManager()
        handler = MockHandler()
        
        # Add a handler
        result = manager.add_handler("test", handler)
        assert result is manager  # Check method chaining
        assert "test" in manager.handlers
        assert manager.handlers["test"] is handler
        
        # Adding duplicate should raise ValueError
        with pytest.raises(ValueError):
            manager.add_handler("test", MockHandler())

    def test_add_invalid_handler(self):
        """Test adding invalid handler."""
        manager = LoggingManager()
        with pytest.raises(ValueError):
            manager.add_handler("test", "not a handler")
    
    def test_remove_handler(self):
        """Test removing handlers."""
        manager = LoggingManager()
        handler = MockHandler()
        
        # Add then remove a handler
        manager.add_handler("test", handler)
        result = manager.remove_handler("test")
        assert result is manager  # Check method chaining
        assert "test" not in manager.handlers
        
        # Removing non-existent handler should raise KeyError
        with pytest.raises(KeyError):
            manager.remove_handler("non_existent")
    
    @patch("logging.getLogger")
    def test_configure(self, mock_get_logger):
        """Test configuration of the root logger."""
        # Setup
        mock_root_logger = MagicMock()
        mock_root_logger.handlers = []
        mock_get_logger.return_value = mock_root_logger
        
        manager = LoggingManager(default_level="INFO")
        handler1 = MockHandler()
        handler2 = MockHandler()
        
        # Add handlers and configure
        manager.add_handler("handler1", handler1)
        manager.add_handler("handler2", handler2)
        manager.configure()
        
        # Verify configuration
        assert manager.is_configured
        mock_get_logger.assert_called_once_with()
        mock_root_logger.setLevel.assert_called_once_with(logging.INFO)
        assert mock_root_logger.addHandler.call_count == 2
    
    def test_get_logger(self):
        """Test getting a logger instance without mocking."""
        # Create a real logger manager with a direct test
        manager = LoggingManager()
        manager.add_handler("test", MockHandler())
        
        # Get a logger
        logger = manager.get_logger("test_module")
        
        # Verify logger setup
        assert manager.is_configured
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module" 