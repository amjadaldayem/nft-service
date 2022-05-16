class SintraException(Exception):
    """Base exception class for Sintra module."""


class ProduceRecordFailedException(SintraException):
    """Raised when client fails to produce record."""


class EnvironmentVariableMissingException(SintraException):
    """Raised when environment variable doesn't exist."""
