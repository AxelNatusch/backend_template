"""
Main FastAPI application initialization.
"""

import logging  # Standard library logging
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

# Module-level logging manager, initialized by init_logging()
_logging_manager: LoggingManager | None = None


def init_logging() -> None:
    """
    Initialize the application logging system.
    This function should be called once when the application starts.
    It configures the module-level _logging_manager.
    """
    global _logging_manager
    if _logging_manager is not None:
        # Logging already initialized
        return

    _logging_manager = LoggingManager()

    # Formatters
    standard_formatter = StandardFormatter()
    json_formatter = JsonFormatter()

    # Determine console log level
    console_log_level = getattr(settings, "LOG_LEVEL_CONSOLE", settings.LOG_LEVEL)

    # Console handler (always added)
    _logging_manager.add_handler(
        "console_json_handler",
        ConsoleHandler(formatter=json_formatter, level=console_log_level),
    )

    # Environment-specific file handlers
    if settings.ENVIRONMENT == "development":
        logs_dir = Path("logs")
        logs_dir.mkdir(parents=True, exist_ok=True)  # Ensure logs directory exists

        dev_log_file = logs_dir / "app_dev.log"
        dev_log_file_jsonl = logs_dir / "app_dev.jsonl"

        _logging_manager.add_handler(
            "dev_file_standard_handler",
            FileHandler(
                filepath=dev_log_file,
                formatter=standard_formatter,
                level=settings.LOG_LEVEL,
            ),
        )
        _logging_manager.add_handler(
            "dev_file_jsonl_handler",
            FileHandler(
                filepath=dev_log_file_jsonl,
                formatter=json_formatter,
                level=settings.LOG_LEVEL,
            ),
        )
    elif settings.ENVIRONMENT == "production":
        # TODO: Implement robust production logging.
        # This might include logging to a centralized service (e.g., ELK, Datadog),
        # ensuring proper log rotation, and potentially different formatting.
        # For now, production will use the console_json_handler configured above.
        # A temporary file logger for production could be added here if needed:
        # logs_dir = Path("logs")
        # logs_dir.mkdir(parents=True, exist_ok=True)
        # prod_log_file = logs_dir / "app_prod.jsonl"
        # _logging_manager.add_handler(
        #     "prod_file_jsonl_handler",
        #     FileHandler(
        #         filepath=prod_log_file,
        #         formatter=json_formatter,
        #         level=settings.LOG_LEVEL,
        #     ),
        # )
        pass  # Explicitly note that console logging is the default for prod for now

    _logging_manager.configure()

    # Initial log message after full configuration
    # Use a temporary logger instance directly from the manager for this first message
    initial_setup_logger = _logging_manager.get_logger("app_setup")
    initial_setup_logger.info(
        f"Logging initialized. Environment: {settings.ENVIRONMENT}, "
        f"Default Log Level: {settings.LOG_LEVEL}, Console Log Level: {console_log_level}"
    )
    if settings.ENVIRONMENT == "production":
        initial_setup_logger.warning(
            "Production logging is currently set to console (JSON). "
            "Review and configure robust production logging as needed."
        )


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger from the application's logging manager.
    Initializes logging on the first call if it hasn't been done yet.

    Args:
        name: Name of the module or component requesting a logger.

    Returns:
        A configured logger instance.
    """
    global _logging_manager
    if _logging_manager is None:
        # Ensures logging is initialized if get_logger is called
        # before explicit initialization (e.g., from other modules at import time).
        init_logging()
        if _logging_manager is None:  # Should be set by init_logging
            raise RuntimeError("Logging manager failed to initialize. This should not happen.")
    return _logging_manager.get_logger(name)


def create_application() -> FastAPI:
    """
    Create, configure, and return the FastAPI application instance.
    """
    # 1. Initialize logging as the very first step
    init_logging()

    # 2. Get a logger for the application creation process
    logger = get_logger(__name__)  # Logger for src.main operations

    # 3. Initialize FastAPI application
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=settings.APP_DESCRIPTION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",  # Standard OpenAPI path
        docs_url=f"{settings.API_V1_STR}/docs",  # Swagger UI
        redoc_url=f"{settings.API_V1_STR}/redoc",  # ReDoc
    )
    logger.info(f"FastAPI application '{settings.APP_NAME}' v{settings.APP_VERSION} initialized.")

    # 4. Initialize Database
    # Consider making create_tables=True configurable via settings for more control
    init_db(create_tables=True)
    logger.info("Database initialized.")

    # 5. Configure CORS (Cross-Origin Resource Sharing)
    if settings.BACKEND_CORS_ORIGINS:
        # Ensure origins are strings, as Pydantic might parse them into other types
        allow_origins_str = [str(origin).strip() for origin in settings.BACKEND_CORS_ORIGINS]
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allow_origins_str,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.info(f"CORS middleware configured for origins: {allow_origins_str}")
    else:
        logger.info("No CORS origins specified. CORS middleware not added.")

    # 6. Include API routers
    app.include_router(api_router)
    logger.info(f"API router included with prefix '{settings.API_V1_STR}'.")

    # 7. Add a root endpoint for basic info and health check
    @app.get("/", tags=["Default"])
    async def root():
        return {
            "application": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "message": "Welcome to the API!",
            "documentation_swagger": app.docs_url,
            "documentation_redoc": app.redoc_url,
        }

    logger.info(f"Root GET endpoint '/' added. Docs at {app.docs_url} and {app.redoc_url}")

    return app


# Create the main application instance by calling the factory function
app = create_application()

# Final startup log message using a logger from the configured system
startup_logger = get_logger(__name__)  # Or get_logger("application_lifecycle")
startup_logger.info(f"'{settings.APP_NAME}' has started successfully in '{settings.ENVIRONMENT}' mode.")
