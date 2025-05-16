"""Base exceptions for the application."""


class ApplicationError(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str = "An error occurred in the application"):
        self.message = message
        super().__init__(self.message)


class DatabaseError(ApplicationError):
    """Exception raised when a database operation fails."""

    def __init__(self, message: str = "Database operation failed"):
        self.message = message
        super().__init__(self.message)
