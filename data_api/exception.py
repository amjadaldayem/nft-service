class SintraDataAPIException(Exception):
    """Base exception class for Data API module."""


class ResourceNotFoundException(SintraDataAPIException):
    """Raised when resource is not found in data storage."""


class DataClientException(SintraDataAPIException):
    """Raised when data client is not able to execute query."""


class EnvironmentVariableMissingException(SintraDataAPIException):
    """Raised when environment variable doesn't exist."""
