"""
Main FastAPI application initialization.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import api_router
from src.core.config.settings import settings
from src.core.db import init_db
from src.core.logging import LoggingManager
from src.core.logging.formatters.json import JsonFormatter
from src.core.logging.formatters.standard import StandardFormatter
from src.core.logging.handlers.console import ConsoleHandler
from src.core.logging.handlers.file import FileHandler
# from src.core.logging.handlers.seq import SeqHandler

# Global logging manager for app-wide use
logging_manager = None
logger = None


def init_logging() -> None:
    """
    Initialize the application logging system based on environment.
    """
    global logging_manager

    # Configure log manager with handlers based on environment
    logging_manager = LoggingManager()

    # Formatters
    standard_formatter = StandardFormatter()
    json_formatter = JsonFormatter()

    # Always add console handler
    logging_manager.add_handler("console", ConsoleHandler(formatter=json_formatter))

    # Add file handler in development
    if settings.ENVIRONMENT == "development":
        # Ensure logs directory exists
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        # log file names
        log_file = "logs/app.log"
        log_file_json = "logs/app.jsonl"

        logging_manager.add_handler(
            "file",
            FileHandler(
                filepath=log_file,
                formatter=standard_formatter,
                level=settings.LOG_LEVEL,
            ),
        )
        logging_manager.add_handler(
            "file_json",
            FileHandler(
                filepath=log_file_json,
                formatter=json_formatter,
                level=settings.LOG_LEVEL,
            ),
        )

    if settings.ENVIRONMENT == "production":
        # setup production logging

        # logging_manager.add_handler(
        #     "seq",
        #     SeqHandler(
        #         seq_url=settings.SEQ_URL,
        #         seq_api_key=settings.SEQ_API_KEY,
        #         log_level=settings.LOG_LEVEL,
        #         batch_size=10,
        #         auto_flush_timeout=30,
        #     )
        # )
        pass

    # Apply configuration
    logging_manager.configure()

    # Get a logger for the main module
    global logger
    logger = logging_manager.get_logger(__name__)
    logger.info(
        f"Application logging initialized. Environment: {settings.ENVIRONMENT}, "
        f"Log level: {settings.LOG_LEVEL}"
    )


def get_logger(name: str):
    """
    Get a configured logger from the application's logging manager.

    Args:
        name: Name of the module requesting a logger

    Returns:
        A configured logger instance
    """
    global logging_manager
    if logging_manager is None:
        init_logging()
    return logging_manager.get_logger(name)


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    """
    # Initialize logging
    init_logging()

    # Initialize FastAPI
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=settings.APP_DESCRIPTION,
        # docs_url=None,
        # redoc_url=None,
    )
    logger.info("FastAPI application initialized")

    # init_db
    init_db(create_tables=True)
    logger.info("Database initialized")

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("CORS configured for origins: %s", settings.BACKEND_CORS_ORIGINS)

    app.include_router(api_router)
    logger.info("API router included")

    # Add root endpoint
    @app.get("/")
    async def root():
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        }

    logger.info("Root endpoint added")

    # Include API router

    return app


app = create_application()
logger.info("Application started")
