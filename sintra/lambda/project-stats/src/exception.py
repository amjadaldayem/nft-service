class ProjectStatsException(Exception):
    """Base exception class for Project Stats module."""


class ProduceRecordFailedException(ProjectStatsException):
    """Raised when client fails to produce record."""


class EnvironmentVariableMissingException(ProjectStatsException):
    """Raised when environment variable doesn't exist."""
