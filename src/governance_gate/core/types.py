"""
Core type definitions for the governance gate system.
"""

from dataclasses import dataclass, field
from typing import Any
from enum import Enum


class DecisionAction(str, Enum):
    """
    Possible governance decision actions.

    Precedence (highest to lowest): STOP > ESCALATE > RESTRICT > ALLOW
    """

    ALLOW = "ALLOW"
    """Safe to proceed autonomously."""

    RESTRICT = "RESTRICT"
    """Respond with constraints, disclaimers, or suggestions only."""

    ESCALATE = "ESCALATE"
    """Require human review or approval."""

    STOP = "STOP"
    """Do not continue due to insufficient authority or information."""

    def __str__(self) -> str:
        return self.value

    @property
    def precedence(self) -> int:
        """Return precedence value (higher = more severe)."""
        return {
            DecisionAction.ALLOW: 0,
            DecisionAction.RESTRICT: 1,
            DecisionAction.ESCALATE: 2,
            DecisionAction.STOP: 3,
        }[self]

    def dominates(self, other: "DecisionAction") -> bool:
        """Return True if this action has higher precedence than other."""
        return self.precedence > other.precedence


@dataclass(frozen=True)
class Intent:
    """
    Represents a recognized user intent.

    Attributes:
        name: The intent identifier (e.g., "order_status_query")
        confidence: Confidence score from intent recognition (0.0 to 1.0)
        parameters: Optional parameters extracted from the user input
    """

    name: str
    confidence: float = 1.0
    parameters: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Intent confidence must be between 0 and 1, got {self.confidence}")


@dataclass(frozen=True)
class Context:
    """
    Represents execution context for the intent.

    Attributes:
        user_id: Identifier for the user (optional)
        channel: Communication channel (e.g., "web", "api", "slack")
        session_id: Session identifier (optional)
        metadata: Additional context information
    """

    user_id: str | None = None
    channel: str | None = None
    session_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Evidence:
    """
    Represents evidence collected for governance evaluation.

    Attributes:
        facts: Information about fact verifiability
        rag: Information about retrieval quality
        topic: Information about the topic and its sensitivity
        metadata: Additional evidence
    """

    facts: dict[str, Any] = field(default_factory=dict)
    rag: dict[str, Any] = field(default_factory=dict)
    topic: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def get(self, path: str, default: Any = None) -> Any:
        """
        Get a value from evidence using dotted path notation.

        Args:
            path: Dotted path (e.g., "facts.verifiable", "rag.confidence")
            default: Default value if path not found

        Returns:
            The value at the path, or default if not found
        """
        parts = path.split(".")
        current: Any = self

        for part in parts:
            if isinstance(current, dict):
                if part not in current:
                    return default
                current = current[part]
            elif hasattr(current, part):
                current = getattr(current, part)
            else:
                return default

        return current
