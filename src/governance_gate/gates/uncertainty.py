"""
Gate that evaluates whether uncertainty is within acceptable bounds.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from governance_gate.core.types import Intent, Context, Evidence, DecisionAction
    from governance_gate.core.pipeline import Gate
    from governance_gate.policy.evaluator import PolicyEvaluator

from governance_gate.core.pipeline import Gate
from governance_gate.core.types import DecisionAction


class UncertaintyGate(Gate):
    """
    Evaluates whether uncertainty is within acceptable bounds.

    Rules:
    - If RAG confidence is below threshold -> RESTRICT
    - If retrieval has conflicting results -> RESTRICT or STOP
    - If knowledge base version is outdated -> RESTRICT
    - If multiple tools disagree -> ESCALATE

    Configuration (via policy):
    - confidence_threshold: Minimum RAG confidence (default: 0.6)
    - stop_on_conflict: If True, STOP on conflicting results (default: False)
    - outdated_version_days: Days after which version is considered outdated
    """

    name = "uncertainty"

    def __init__(
        self,
        confidence_threshold: float = 0.6,
        stop_on_conflict: bool = False,
        outdated_version_days: int = 30,
    ) -> None:
        """
        Initialize the gate.

        Args:
            confidence_threshold: Minimum confidence threshold for RAG
            stop_on_conflict: Whether to STOP (vs RESTRICT) on conflicting results
            outdated_version_days: Days after which version is outdated
        """
        self.confidence_threshold = confidence_threshold
        self.stop_on_conflict = stop_on_conflict
        self.outdated_version_days = outdated_version_days

    def evaluate(
        self,
        intent: "Intent",
        context: "Context",
        evidence: "Evidence",
        policy: "PolicyEvaluator | None" = None,
    ) -> tuple["DecisionAction | None", str]:
        """
        Evaluate uncertainty levels.

        Returns:
            (DecisionAction, rationale) - Action is None if no override needed
        """
        # Check if policy overrides defaults
        if policy:
            policy_config = policy.get_gate_config(self.name)
            if policy_config:
                self.confidence_threshold = policy_config.get(
                    "confidence_threshold", self.confidence_threshold
                )
                self.stop_on_conflict = policy_config.get(
                    "stop_on_conflict", self.stop_on_conflict
                )
                self.outdated_version_days = policy_config.get(
                    "outdated_version_days", self.outdated_version_days
                )

        # Get RAG confidence from evidence
        rag_confidence = evidence.get("rag.confidence", 1.0)
        rag_source = evidence.get("rag.source", "unknown")

        # Rule 1: Low RAG confidence
        if rag_confidence < self.confidence_threshold:
            return (
                DecisionAction.RESTRICT,
                f"Retrieval confidence {rag_confidence:.2f} is below threshold {self.confidence_threshold:.2f} (source: {rag_source})",
            )

        # Check for conflicting results
        has_conflicts = evidence.get("rag.has_conflicts", False)
        conflict_count = evidence.get("rag.conflict_count", 0)

        if has_conflicts or conflict_count > 0:
            action = DecisionAction.STOP if self.stop_on_conflict else DecisionAction.RESTRICT
            return (
                action,
                f"Retrieval has {conflict_count} conflicting results - cannot determine correct answer",
            )

        # Check knowledge version
        kb_version = evidence.get("rag.kb_version", "unknown")
        kb_age_days = evidence.get("rag.kb_age_days", 0)

        if kb_age_days > self.outdated_version_days:
            return (
                DecisionAction.RESTRICT,
                f"Knowledge base version {kb_version} is {kb_age_days} days old (outdated threshold: {self.outdated_version_days} days)",
            )

        # Check for tool disagreement
        tool_disagreement = evidence.get("rag.tool_disagreement", False)
        if tool_disagreement:
            return (
                DecisionAction.ESCALATE,
                "Multiple tools provided conflicting results - requires human review",
            )

        # Check retrieval coverage
        retrieval_coverage = evidence.get("rag.coverage", 1.0)
        coverage_threshold = evidence.get("rag.coverage_threshold", 0.8)

        if retrieval_coverage < coverage_threshold:
            return (
                DecisionAction.RESTRICT,
                f"Retrieval coverage {retrieval_coverage:.2f} is incomplete (threshold: {coverage_threshold:.2f})",
            )

        # No issues found
        return (
            None,
            f"Uncertainty is acceptable (confidence: {rag_confidence:.2f}, coverage: {retrieval_coverage:.2f})",
        )

    def get_config_snapshot(self) -> dict[str, Any]:
        """Get the configuration snapshot of this gate."""
        return {
            "confidence_threshold": self.confidence_threshold,
            "stop_on_conflict": self.stop_on_conflict,
            "outdated_version_days": self.outdated_version_days,
        }

    def get_input_summary(self, evidence: "Evidence") -> dict[str, Any]:
        """Get the input summary (evidence slice) that this gate examined."""
        # This gate examines the rag namespace
        return {
            "rag": {
                "confidence": evidence.rag.get("confidence"),
                "source": evidence.rag.get("source"),
                "has_conflicts": evidence.rag.get("has_conflicts"),
                "conflict_count": evidence.rag.get("conflict_count"),
                "kb_version": evidence.rag.get("kb_version"),
                "kb_age_days": evidence.rag.get("kb_age_days"),
                "coverage": evidence.rag.get("coverage"),
                "tool_disagreement": evidence.rag.get("tool_disagreement"),
            }
        }
