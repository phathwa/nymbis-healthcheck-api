"""Custom exceptions for EC2 health checks."""


class InstanceNotFoundError(Exception):
    """Raised when an EC2 instance cannot be found."""
