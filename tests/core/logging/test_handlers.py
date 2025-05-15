import logging
import os
import tempfile
from io import StringIO
from unittest.mock import patch, MagicMock

from src.core.logging.formatters import StandardFormatter, JsonFormatter
from src.core.logging.handlers import ConsoleHandler, FileHandler, SeqHandler


class TestConsoleHandler:
    """Tests for the ConsoleHandler class."""
    
    def test_get_handler(self):
        """Test that get_handler returns a Handler instance."""
        handler = ConsoleHandler().get_handler()
        assert isinstance(handler, logging.Handler)
        assert isinstance(handler, logging.StreamHandler)
    
    def test_with_formatter(self):
        """Test that the handler uses the provided formatter."""
        formatter = StandardFormatter()
        handler = ConsoleHandler(formatter=formatter).get_handler()
        
        # Check that a formatter is set
        assert handler.formatter is not None
        # We can't test for identity since get_formatter() creates a new instance
        # Instead check the formatter class is what we expect
        assert handler.formatter.__class__ == formatter.get_formatter().__class__
    
    def test_with_level(self):
        """Test that the handler respects the provided level."""
        level = "WARNING"
        handler = ConsoleHandler(level=level).get_handler()
        
        # Check that the level is set correctly
        assert handler.level == getattr(logging, level)
    
    def test_with_custom_stream(self, enable_logging):
        """Test that the handler uses the provided stream."""
        stream = StringIO()
        handler = ConsoleHandler(stream=stream).get_handler()
        
        # Create and configure a logger that uses our handler
        logger = logging.getLogger("test_console_handler")
        logger.setLevel(logging.INFO)
        logger.handlers = [handler]
        
        # Log a message
        test_message = "Test console message"
        logger.info(test_message)
        
        # Check that the message was written to our stream
        assert test_message in stream.getvalue()


class TestFileHandler:
    """Tests for the FileHandler class."""
    
    def test_get_handler(self):
        """Test that get_handler returns a Handler instance."""
        with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as tmp:
            try:
                handler = FileHandler(filepath=tmp.name).get_handler()
                assert isinstance(handler, logging.Handler)
                assert isinstance(handler, logging.handlers.RotatingFileHandler)
            finally:
                os.unlink(tmp.name)
    
    def test_with_formatter(self):
        """Test that the handler uses the provided formatter."""
        formatter = JsonFormatter()
        with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as tmp:
            try:
                handler = FileHandler(filepath=tmp.name, formatter=formatter).get_handler()
                
                # Check that a formatter is set
                assert handler.formatter is not None
                assert handler.formatter.__class__ == formatter.get_formatter().__class__
            finally:
                os.unlink(tmp.name)
    
    def test_with_level(self):
        """Test that the handler respects the provided level."""
        level = "ERROR"
        with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as tmp:
            try:
                handler = FileHandler(filepath=tmp.name, level=level).get_handler()
                
                # Check that the level is set correctly
                assert handler.level == getattr(logging, level)
            finally:
                os.unlink(tmp.name)
    
    def test_log_to_file(self, enable_logging):
        """Test that logs are written to the specified file."""
        with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as tmp:
            try:
                # Create handler and logger
                handler = FileHandler(filepath=tmp.name).get_handler()
                logger = logging.getLogger("test_file_handler")
                logger.setLevel(logging.INFO)
                logger.handlers = [handler]
                
                # Log a message
                test_message = "Test file message"
                logger.info(test_message)
                
                # Ensure the message is flushed to disk
                handler.flush()
                
                # Read the file and check the message
                with open(tmp.name, 'r') as f:
                    content = f.read()
                    assert test_message in content
            finally:
                os.unlink(tmp.name)
    
    def test_directory_creation(self):
        """Test that the log directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_dir = os.path.join(tmp_dir, "logs")
            log_file = os.path.join(log_dir, "test.log")
            
            # Directory shouldn't exist yet
            assert not os.path.exists(log_dir)
            
            # Creating the handler should create the directory
            FileHandler(filepath=log_file).get_handler()
            
            # Check directory was created
            assert os.path.exists(log_dir)


class TestSeqHandler:
    """Tests for the SeqHandler class."""
    
    @patch('src.core.logging.handlers.seq.SeqLogHandler')
    def test_get_handler(self, mock_seq_handler):
        """Test that get_handler returns a properly configured SeqLogHandler."""
        # Setup mock
        mock_instance = MagicMock()
        mock_seq_handler.return_value = mock_instance
        
        # Create handler
        SeqHandler(
            seq_url="http://test-seq-server:5341", 
            seq_api_key="test-api-key",
            log_level="WARNING"
        ).get_handler()
        
        # Verify SeqLogHandler was created with correct parameters
        mock_seq_handler.assert_called_once_with(
            server_url="http://test-seq-server:5341",
            api_key="test-api-key",
            batch_size=10,
            auto_flush_timeout=None
        )
        
        # Verify level was set
        assert mock_instance.setLevel.called
    
    @patch('src.core.logging.handlers.seq.SeqLogHandler') 
    def test_log_level_setting(self, mock_seq_handler):
        """Test that the log level is properly set."""
        # Setup a mock
        mock_instance = MagicMock()
        mock_seq_handler.return_value = mock_instance
        
        # Create handler with a specific log level
        SeqHandler(
            seq_url="http://test-seq-server:5341",
            log_level="ERROR"
        ).get_handler()
        
        # Verify the log level was set correctly
        mock_instance.setLevel.assert_called_once_with("ERROR") 