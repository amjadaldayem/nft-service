class SintraException(Exception):
    """Base exception class for Sintra module."""


class ProduceRecordFailedException(SintraException):
    """Raised when client fails to produce record."""


class EnvironmentVariableMissingException(SintraException):
    """Raised when environment variable doesn't exist."""


class DecodingException(SintraException):
    """Raised when input record fails decoding process."""


class TransactionParserNotFoundException(SintraException):
    """Raised when transaction parser doesn't exist for market account."""


class TransactionInstructionMissingException(SintraException):
    """Raised when transaction doesn'have inner instructions supported by program account."""


class UnknownTransactionException(SintraException):
    """Raised when parser doesn't support transaction type."""


class SecondaryMarketDataMissingException(SintraException):
    """Raised when there is not sufficient data to create SME."""
