"""
Exception classes for the governance gate system.
"""


class GovernanceError(Exception):
    """Base exception for all governance-related errors."""

    pass


class PolicyError(GovernanceError):
    """Raised when policy loading or validation fails."""

    pass


class GateError(GovernanceError):
    """Raised when a gate evaluation fails."""

    pass


class ValidationError(GovernanceError):
    """Raised when input validation fails."""

    pass
