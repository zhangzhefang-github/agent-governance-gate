"""
Gate that evaluates whether facts used in the response are verifiable.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from governance_gate.core.types import Intent, Context, Evidence, DecisionAction
    from governance_gate.core.pipeline import Gate
    from governance_gate.policy.evaluator import PolicyEvaluator

from governance_gate.core.pipeline import Gate
from governance_gate.core.types import DecisionAction


class FactVerifiabilityGate(Gate):
    """
    Evaluates whether facts required to fulfill the intent are verifiable.

    Rules:
    - If facts are not verifiable and intent requires real-time facts -> RESTRICT or STOP
    - If facts are stale or outdated -> RESTRICT
    - If facts are from untrusted sources -> RESTRICT

    Configuration (via policy):
    - require_realtime_facts: List of intent names that require real-time facts
    - verifiable_threshold: Minimum confidence for fact verifiability (default: 0.7)
    - stop_on_unverifiable: If True, STOP instead of RESTRICT for unverifiable facts
    """

    name = "fact_verifiability"

    def __init__(
        self,
        require_realtime_facts: list[str] | None = None,
        verifiable_threshold: float = 0.7,
        stop_on_unverifiable: bool = False,
    ) -> None:
        """
        Initialize the gate.

        Args:
            require_realtime_facts: Intent names that require real-time facts
            verifiable_threshold: Minimum threshold for verifiable confidence
            stop_on_unverifiable: Whether to STOP (vs RESTRICT) on unverifiable facts
        """
        self.require_realtime_facts = set(require_realtime_facts or [])
        self.verifiable_threshold = verifiable_threshold
        self.stop_on_unverifiable = stop_on_unverifiable

    def evaluate(
        self,
        intent: "Intent",
        context: "Context",
        evidence: "Evidence",
        policy: "PolicyEvaluator | None" = None,
    ) -> tuple["DecisionAction | None", str]:
        """
        Evaluate fact verifiability.

        Returns:
            (DecisionAction, rationale) - Action is None if no override needed
        """
        # Check if policy overrides defaults
        if policy:
            policy_config = policy.get_gate_config(self.name)
            if policy_config:
                self.require_realtime_facts = set(
                    policy_config.get("require_realtime_facts", self.require_realtime_facts)
                )
                self.verifiable_threshold = policy_config.get(
                    "verifiable_threshold", self.verifiable_threshold
                )
                self.stop_on_unverifiable = policy_config.get(
                    "stop_on_unverifiable", self.stop_on_unverifiable
                )

        # Get fact verifiability from evidence
        verifiable = evidence.get("facts.verifiable", True)
        verifiable_confidence = evidence.get("facts.verifiable_confidence", 1.0)

        # Check if this intent requires real-time facts
        needs_realtime = intent.name in self.require_realtime_facts
        is_realtime_dependent = evidence.get("facts.requires_realtime", needs_realtime)

        # Get fact source info
        fact_source = evidence.get("facts.source", "unknown")
        fact_freshness = evidence.get("facts.freshness", "unknown")

        # Rule 1: Facts are explicitly not verifiable
        if verifiable is False:
            if is_realtime_dependent:
                action = DecisionAction.STOP if self.stop_on_unverifiable else DecisionAction.RESTRICT
                return (
                    action,
                    f"Intent '{intent.name}' requires real-time facts but facts are not verifiable (source: {fact_source}, freshness: {fact_freshness})",
                )
            else:
                return (
                    DecisionAction.RESTRICT,
                    f"Facts are not verifiable (source: {fact_source}, confidence: {verifiable_confidence:.2f})",
                )

        # Rule 2: Facts have low verifiability confidence
        if verifiable_confidence < self.verifiable_threshold:
            if is_realtime_dependent:
                return (
                    DecisionAction.RESTRICT,
                    f"Intent '{intent.name}' requires high-confidence facts, but confidence is {verifiable_confidence:.2f} (threshold: {self.verifiable_threshold:.2f})",
                )
            else:
                return (
                    None,
                    f"Fact verifiability confidence is {verifiable_confidence:.2f} (below threshold {self.verifiable_threshold:.2f})",
                )

        # Rule 3: Facts are from untrusted sources
        if fact_source in ["unknown", "untrusted", "user_provided"]:
            if is_realtime_dependent:
                return (
                    DecisionAction.RESTRICT,
                    f"Intent '{intent.name}' requires trusted sources, but source is '{fact_source}'",
                )
            else:
                return (
                    None,
                    f"Fact source is '{fact_source}' - consider verification",
                )

        # Rule 4: Facts may be stale
        if fact_freshness in ["stale", "outdated", "expired"]:
            return (
                DecisionAction.RESTRICT,
                f"Facts may be stale (freshness: {fact_freshness}) - recommend refresh",
            )

        # No issues found
        return (
            None,
            f"Facts are verifiable (confidence: {verifiable_confidence:.2f}, source: {fact_source})",
        )

    def get_config_snapshot(self) -> dict[str, Any]:
        """Get the configuration snapshot of this gate."""
        return {
            "verifiable_threshold": self.verifiable_threshold,
            "require_realtime_facts": list(self.require_realtime_facts),
            "stop_on_unverifiable": self.stop_on_unverifiable,
        }

    def get_input_summary(self, evidence: "Evidence") -> dict[str, Any]:
        """Get the input summary (evidence slice) that this gate examined."""
        # This gate examines the facts namespace
        return {
            "facts": {
                "verifiable": evidence.facts,
                "verifiable_confidence": evidence.facts.get("verifiable_confidence"),
                "source": evidence.facts.get("source"),
                "freshness": evidence.facts.get("freshness"),
                "requires_realtime": evidence.facts.get("requires_realtime"),
            }
        }
