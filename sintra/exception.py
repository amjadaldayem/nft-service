class SintraException(Exception):
    """Base exception class for Sintra module."""


class ClientRPCConnectionException(SintraException):
    """Raised when there is problem with connection to RPC client."""


class ClientRPCConnectionClosedException(SintraException):
    """Raised when client connection is unexpectedly closed."""


class ProduceRecordFailedException(SintraException):
    """Raised when client fails to produce record."""


class EnvironmentVariableMissingException(SintraException):
    """Raised when environment variable doesn't exist."""
