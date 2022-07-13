class TwitterTrendsException(Exception):
    """Base exception class for Twitter Trends module."""


class ProduceRecordFailedException(TwitterTrendsException):
    """Raised when client fails to produce record."""


class EnvironmentVariableMissingException(TwitterTrendsException):
    """Raised when environment variable doesn't exist."""
