class SintraException(Exception):
    """Base exception class for Sintra module."""


class ProduceRecordFailedException(SintraException):
    """Raised when client fails to produce record."""


class EnvironmentVariableMissingException(SintraException):
    """Raised when environment variable doesn't exist."""


class DecodingException(SintraException):
    """Raised when input record fails decoding process."""


class FetchTokenDataException(SintraException):
    """Raised when fetching token data fails or times out."""


class UnknownBlockchainException(SintraException):
    """Raised when blockchain id is unknown."""
