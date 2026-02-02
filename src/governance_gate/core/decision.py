"""
Core decision model with enhanced traceability.

Enhanced with:
- policy_version, policy_name
- gate_decisions (with config_used and input_summary)
- decision_code (stable code for aggregation)
"""

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING, Optional
from datetime import datetime, timezone
import uuid

if TYPE_CHECKING:
    from .types import DecisionAction


def generate_trace_id() -> str:
    """Generate a unique trace identifier."""
    return str(uuid.uuid4())


def generate_decision_code(action: "DecisionAction", primary_gate: str, reason_type: str) -> str:
    """
    Generate a stable decision code for aggregation.

    Format: GATE_ACTION_REASON

    Examples:
        FACTS_ALLOW_VERIFIED
        FACTS_RESTRICT_UNVERIFIABLE
        RESPONSIBILITY_ESCALATE_FINANCIAL
        SAFETY_STOP_FRAUD

    Args:
        action: The decision action
        primary_gate: Name of the primary gate causing the decision
        reason_type: Short reason identifier

    Returns:
        Stable decision code
    """
    gate_prefix = {
        "fact_verifiability": "FACTS",
        "uncertainty": "UNCERTAINTY",
        "responsibility": "RESPONSIBILITY",
        "safety": "SAFETY",
    }.get(primary_gate, "GOVERNANCE")

    action_upper = action.value.upper()
    reason_upper = reason_type.upper().replace(" ", "_")

    return f"{gate_prefix}_{action_upper}_{reason_upper}"


@dataclass
class GateDecision:
    """
    Decision contribution from a single gate.

    Enhanced with traceability for audit.
    """

    gate_name: str
    suggested_action: Optional[str]  # None if gate didn't trigger
    rationale: str
    config_used: Optional[dict[str, Any]] = None  # Thresholds used (e.g., {"confidence": 0.7})
    input_summary: Optional[dict[str, Any]] = None  # Evidence slice this gate examined

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "gate_name": self.gate_name,
            "suggested_action": self.suggested_action,
            "rationale": self.rationale,
            "config_used": self.config_used,
            "input_summary": self.input_summary,
        }


@dataclass
class Decision:
    """
    Represents a governance decision with enhanced traceability.

    Attributes:
        action: The decision action (ALLOW/RESTRICT/ESCALATE/STOP)
        rationale: Human-readable explanation of the decision
        evidence_summary: Structured summary of evidence considered
        trace_id: Unique identifier for tracing and audit
        required_steps: Optional list of required next steps
        timestamp: When the decision was made
        gate_contributions: Which gates contributed to this decision (backward compat)
        gate_decisions: Per-gate decisions with traceability (enhanced)
        policy_version: Version of policy used (if any)
        policy_name: Name of policy used (if any)
        decision_code: Stable machine-readable code for aggregation
        final_gate: Name of gate that determined final action (None for ALLOW)

    Enhanced in Iteration 2 to support:
    - Audit trails (which gate blocked, with what evidence)
    - Log aggregation (decision_code for grouping)
    - Policy regression (policy_version tracking)

    Enhanced in Iteration 4 (finalization) to support:
    - Explicit gate authority (final_gate answers "who blocked")
    """

    action: "DecisionAction"
    rationale: str
    evidence_summary: dict[str, Any]
    trace_id: str = field(default_factory=generate_trace_id)
    required_steps: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Backward compatibility
    gate_contributions: dict[str, str] = field(default_factory=dict)

    # Enhanced traceability fields
    gate_decisions: dict[str, GateDecision] = field(default_factory=dict)
    policy_version: Optional[str] = None
    policy_name: Optional[str] = None
    decision_code: Optional[str] = None
    final_gate: Optional[str] = None  # Name of gate that determined the final action (None for ALLOW)

    def add_gate_decision(
        self,
        gate_name: str,
        suggested_action: Optional[str],
        rationale: str,
        config_used: Optional[dict[str, Any]] = None,
        input_summary: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Add a gate decision to the trace.

        Args:
            gate_name: Name of the gate
            suggested_action: Action suggested by gate (None if no override)
            rationale: Rationale from the gate
            config_used: Configuration/thresholds used
            input_summary: Evidence slice this gate examined
        """
        # Add to new structure
        self.gate_decisions[gate_name] = GateDecision(
            gate_name=gate_name,
            suggested_action=suggested_action,
            rationale=rationale,
            config_used=config_used,
            input_summary=input_summary,
        )

        # Maintain backward compatibility
        self.gate_contributions[gate_name] = rationale

    def add_annotation(self, gate_name: str, rationale: str) -> None:
        """
        Add an annotation from a gate without changing the action (backward compat).

        Args:
            gate_name: Name of the gate providing the annotation
            rationale: The annotation rationale
        """
        self.add_gate_decision(gate_name, None, rationale)

    def override(
        self,
        new_action: "DecisionAction",
        gate_name: str,
        rationale: str,
        config_used: Optional[dict[str, Any]] = None,
        input_summary: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Override the current decision with a new action.

        Args:
            new_action: The new decision action
            gate_name: Name of the gate requesting the override
            rationale: Rationale for the override
            config_used: Configuration used
            input_summary: Evidence slice examined
        """
        self.action = new_action
        self.add_gate_decision(
            gate_name=gate_name,
            suggested_action=new_action.value,
            rationale=rationale,
            config_used=config_used,
            input_summary=input_summary,
        )
        self.rationale = rationale

    def set_decision_code(self, code: str) -> None:
        """Set the decision code for aggregation."""
        self.decision_code = code

    def set_policy_info(self, policy_name: str, policy_version: str) -> None:
        """Set policy information."""
        self.policy_name = policy_name
        self.policy_version = policy_version

    def to_dict(self) -> dict[str, Any]:
        """Convert decision to dictionary for serialization."""
        return {
            "action": self.action.value,
            "rationale": self.rationale,
            "evidence_summary": self.evidence_summary,
            "trace_id": self.trace_id,
            "required_steps": self.required_steps,
            "timestamp": self.timestamp,
            "gate_contributions": self.gate_contributions,  # Backward compat
            "gate_decisions": {
                name: gd.to_dict() for name, gd in self.gate_decisions.items()
            },
            "policy_version": self.policy_version,
            "policy_name": self.policy_name,
            "decision_code": self.decision_code,
            "final_gate": self.final_gate,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Decision":
        """Create a Decision from a dictionary."""
        from .types import DecisionAction

        decision = cls(
            action=DecisionAction(data["action"]),
            rationale=data["rationale"],
            evidence_summary=data.get("evidence_summary", {}),
            trace_id=data.get("trace_id", generate_trace_id()),
            required_steps=data.get("required_steps", []),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            gate_contributions=data.get("gate_contributions", {}),
            policy_version=data.get("policy_version"),
            policy_name=data.get("policy_name"),
            decision_code=data.get("decision_code"),
            final_gate=data.get("final_gate"),
        )

        # Restore gate_decisions if present
        if "gate_decisions" in data:
            for gate_name, gd_dict in data["gate_decisions"].items():
                decision.gate_decisions[gate_name] = GateDecision(
                    gate_name=gd_dict["gate_name"],
                    suggested_action=gd_dict.get("suggested_action"),
                    rationale=gd_dict["rationale"],
                    config_used=gd_dict.get("config_used"),
                    input_summary=gd_dict.get("input_summary"),
                )

        return decision


# Import DecisionAction at module level to avoid circular import
from governance_gate.core.types import DecisionAction
