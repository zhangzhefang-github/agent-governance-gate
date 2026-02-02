"""
Governance pipeline that runs gates and combines their decisions deterministically.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any
import copy

if TYPE_CHECKING:
    from governance_gate.core.types import Intent, Context, Evidence, DecisionAction
    from governance_gate.core.decision import Decision
    from governance_gate.policy.evaluator import PolicyEvaluator


class Gate(ABC):
    """
    Abstract base class for governance gates.

    Each gate evaluates the intent, context, and evidence to determine
    if the action should be modified (overridden) or annotated.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this gate."""
        pass

    @abstractmethod
    def evaluate(
        self,
        intent: "Intent",
        context: "Context",
        evidence: "Evidence",
        policy: "PolicyEvaluator | None" = None,
    ) -> tuple["DecisionAction | None", str]:
        """
        Evaluate the gate and return a decision.

        Returns:
            A tuple of (action, rationale):
            - action: The decision action (ALLOW/RESTRICT/ESCALATE/STOP) if the gate
              wants to override, or None to continue with current decision
            - rationale: Human-readable explanation

        Note:
            Returning (None, rationale) will annotate the decision without changing the action.
            Returning (action, rationale) with an action will override the current action.
        """
        pass

    def get_config_snapshot(self) -> dict[str, Any]:
        """
        Get the current configuration snapshot of this gate.

        Returns a dictionary of config values that were used during evaluation.
        This should be called after evaluate() to capture the actual config used.
        """
        # Default implementation - subclasses can override
        return {}

    def get_input_summary(self, evidence: "Evidence") -> dict[str, Any]:
        """
        Get the input summary (evidence slice) that this gate examined.

        Args:
            evidence: The full evidence object

        Returns:
            A dictionary containing only the evidence fields this gate examined
        """
        # Default implementation - subclasses should override to be more specific
        # This prevents the "not accessed" warning
        _ = evidence  # Mark as intentionally unused for now
        return {}


class GovernancePipeline:
    """
    Main governance pipeline that runs gates in order and combines decisions.

    The pipeline follows deterministic precedence:
    STOP > ESCALATE > RESTRICT > ALLOW

    Gates are evaluated in sequence. Each gate can:
    1. Return None to continue with the current decision
    2. Return a DecisionAction to override, if it has higher precedence
    3. Add annotations regardless of action
    """

    def __init__(self, gates: list[Gate], default_action: "DecisionAction" = None) -> None:
        """
        Initialize the pipeline with a list of gates.

        Args:
            gates: List of gates to evaluate in order
            default_action: Default action if no gates override (default: ALLOW)
        """
        from governance_gate.core.types import DecisionAction

        self.gates = gates
        self.default_action = default_action or DecisionAction.ALLOW

    def evaluate(
        self,
        intent: "Intent",
        context: "Context",
        evidence: "Evidence",
        policy: "PolicyEvaluator | None" = None,
    ) -> "Decision":
        """
        Run all gates and produce a final decision.

        Args:
            intent: The recognized user intent
            context: Execution context
            evidence: Collected evidence for evaluation
            policy: Optional policy evaluator for rule-based decisions

        Returns:
            A Decision with the final action, rationale, and evidence summary
        """
        from governance_gate.core.decision import Decision, generate_decision_code
        from governance_gate.core.types import DecisionAction

        # Start with default decision
        current_action = self.default_action
        winning_gate = None  # Tracks which gate's action is currently winning
        decision = Decision(
            action=current_action,
            rationale="No gates triggered",
            evidence_summary={
                "intent": intent.name,
                "context": {
                    "channel": context.channel,
                    "user_id": context.user_id,
                },
                "evidence_keys": list(evidence.metadata.keys()),
            },
        )

        # Set policy info if provided
        if policy:
            policy_dict = policy.policy
            decision.set_policy_info(
                policy_name=policy_dict.get("name"),
                policy_version=policy_dict.get("version"),
            )

        # Track primary gate for decision code generation
        primary_gate = None
        primary_reason_type = "default"

        # Evaluate each gate in sequence
        for gate in self.gates:
            gate_action, gate_rationale = gate.evaluate(intent, context, evidence, policy)

            # Capture traceability info
            config_used = gate.get_config_snapshot()
            input_summary = gate.get_input_summary(evidence)

            # Add gate decision with traceability
            decision.add_gate_decision(
                gate_name=gate.name,
                suggested_action=gate_action.value if gate_action else None,
                rationale=gate_rationale,
                config_used=config_used if config_used else None,
                input_summary=input_summary if input_summary else None,
            )

            # Override action if gate returned one with higher precedence
            if gate_action is not None:
                if gate_action.dominates(decision.action):
                    decision.override(gate_action, gate.name, gate_rationale, config_used, input_summary)
                    winning_gate = gate.name  # Track the gate that's currently winning
                    primary_gate = gate.name
                    primary_reason_type = gate_rationale.split()[0] if gate_rationale else "override"

        # Set final_gate: None for ALLOW, otherwise the winning gate name
        if decision.action != DecisionAction.ALLOW:
            decision.final_gate = winning_gate
        else:
            decision.final_gate = None

        # Generate decision code based on final action and primary gate
        if primary_gate:
            decision_code = generate_decision_code(decision.action, primary_gate, primary_reason_type)
            decision.set_decision_code(decision_code)
        else:
            # Default decision code
            decision_code = f"GOVERNANCE_{decision.action.value}_DEFAULT"
            decision.set_decision_code(decision_code)

        return decision

    def add_gate(self, gate: Gate) -> None:
        """Add a gate to the end of the pipeline."""
        self.gates.append(gate)

    def remove_gate(self, gate_name: str) -> bool:
        """Remove a gate by name. Returns True if found and removed."""
        original_length = len(self.gates)
        self.gates = [g for g in self.gates if g.name != gate_name]
        return len(self.gates) < original_length
