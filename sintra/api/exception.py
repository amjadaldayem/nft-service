class SintraDataAPIException(Exception):
    """Base exception class for Data API module."""


class ResourceNotFoundException(SintraDataAPIException):
    """Raised when resource is not found in data storage."""
