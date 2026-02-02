"""
Agent Governance Gate

A framework-agnostic governance gate for Agent systems that decides whether
an action is ALLOW, RESTRICT, ESCALATE, or STOP based on:
- Fact verifiability
- Uncertainty exposure
- Responsibility boundary
"""

from governance_gate.core.types import (
    Intent,
    Context,
    Evidence,
    DecisionAction,
)
from governance_gate.core.decision import Decision
from governance_gate.core.pipeline import GovernancePipeline
from governance_gate.core.errors import (
    GovernanceError,
    PolicyError,
    GateError,
    ValidationError,
)

__version__ = "0.1.0"

__all__ = [
    "Intent",
    "Context",
    "Evidence",
    "Decision",
    "DecisionAction",
    "GovernancePipeline",
    "GovernanceError",
    "PolicyError",
    "GateError",
    "ValidationError",
    "__version__",
]
