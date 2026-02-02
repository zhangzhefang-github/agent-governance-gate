"""
Gate that evaluates whether responsibility boundaries are respected.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from governance_gate.core.types import Intent, Context, Evidence, DecisionAction
    from governance_gate.core.pipeline import Gate
    from governance_gate.policy.evaluator import PolicyEvaluator

from governance_gate.core.pipeline import Gate
from governance_gate.core.types import DecisionAction


class ResponsibilityGate(Gate):
    """
    Evaluates whether the request crosses responsibility boundaries.

    Rules:
    - If intent has financial impact -> ESCALATE
    - If intent requires authority/commitment -> ESCALATE
    - If intent is irreversible -> ESCALATE
    - If intent is in sensitive list -> ESCALATE or STOP

    Configuration (via policy):
    - financial_intents: List of intent names that have financial impact
    - authority_intents: List of intent names requiring authority
    - sensitive_intents: List of intent names that are sensitive
    - stop_on_sensitive: If True, STOP (vs ESCALATE) on sensitive intents
    """

    name = "responsibility"

    def __init__(
        self,
        financial_intents: list[str] | None = None,
        authority_intents: list[str] | None = None,
        sensitive_intents: list[str] | None = None,
        stop_on_sensitive: bool = False,
    ) -> None:
        """
        Initialize the gate.

        Args:
            financial_intents: Intent names that have financial impact
            authority_intents: Intent names requiring authority
            sensitive_intents: Intent names that are sensitive
            stop_on_sensitive: Whether to STOP (vs ESCALATE) on sensitive intents
        """
        self.financial_intents = set(financial_intents or [
            "refund",
            "compensation",
            "discount_approval",
            "credit_request",
            "payment_adjustment",
        ])
        self.authority_intents = set(authority_intents or [
            "policy_change",
            "contract_modification",
            "commitment",
            "guarantee",
        ])
        self.sensitive_intents = set(sensitive_intents or [
            "legal_advice",
            "medical_advice",
            "regulatory_compliance",
        ])
        self.stop_on_sensitive = stop_on_sensitive

    def evaluate(
        self,
        intent: "Intent",
        context: "Context",
        evidence: "Evidence",
        policy: "PolicyEvaluator | None" = None,
    ) -> tuple["DecisionAction | None", str]:
        """
        Evaluate responsibility boundaries.

        Returns:
            (DecisionAction, rationale) - Action is None if no override needed
        """
        # Check if policy overrides defaults
        if policy:
            policy_config = policy.get_gate_config(self.name)
            if policy_config:
                self.financial_intents = set(
                    policy_config.get("financial_intents", list(self.financial_intents))
                )
                self.authority_intents = set(
                    policy_config.get("authority_intents", list(self.authority_intents))
                )
                self.sensitive_intents = set(
                    policy_config.get("sensitive_intents", list(self.sensitive_intents))
                )
                self.stop_on_sensitive = policy_config.get(
                    "stop_on_sensitive", self.stop_on_sensitive
                )

        # Check evidence flags
        has_financial_impact = evidence.get("topic.has_financial_impact", False)
        requires_authority = evidence.get("topic.requires_authority", False)
        is_irreversible = evidence.get("topic.is_irreversible", False)
        is_sensitive = evidence.get("topic.is_sensitive", False)

        # Rule 1: Financial impact
        if (
            intent.name in self.financial_intents
            or has_financial_impact
        ):
            return (
                DecisionAction.ESCALATE,
                f"Intent '{intent.name}' has financial responsibility - requires human review",
            )

        # Rule 2: Requires authority/commitment
        if (
            intent.name in self.authority_intents
            or requires_authority
        ):
            return (
                DecisionAction.ESCALATE,
                f"Intent '{intent.name}' requires organizational authority - cannot commit autonomously",
            )

        # Rule 3: Irreversible action
        if is_irreversible:
            return (
                DecisionAction.ESCALATE,
                f"Intent '{intent.name}' is irreversible - requires explicit approval",
            )

        # Rule 4: Sensitive topic
        if (
            intent.name in self.sensitive_intents
            or is_sensitive
        ):
            action = DecisionAction.STOP if self.stop_on_sensitive else DecisionAction.ESCALATE
            return (
                action,
                f"Intent '{intent.name}' involves sensitive topic - outside autonomous scope",
            )

        # Check for compensation keywords in parameters
        params = intent.parameters or {}
        user_input = params.get("user_input", "").lower()
        compensation_keywords = ["compensat", "refund", "credit", "discount", "reimburse"]

        if any(keyword in user_input for keyword in compensation_keywords):
            return (
                DecisionAction.ESCALATE,
                "User input suggests compensation/financial request - requires human review",
            )

        # No issues found
        return (
            None,
            f"Intent '{intent.name}' is within responsibility boundaries",
        )

    def get_config_snapshot(self) -> dict[str, Any]:
        """Get the configuration snapshot of this gate."""
        return {
            "financial_intents": list(self.financial_intents),
            "authority_intents": list(self.authority_intents),
            "sensitive_intents": list(self.sensitive_intents),
            "stop_on_sensitive": self.stop_on_sensitive,
        }

    def get_input_summary(self, evidence: "Evidence") -> dict[str, Any]:
        """Get the input summary (evidence slice) that this gate examined."""
        # This gate examines the topic namespace and intent name
        return {
            "topic": {
                "has_financial_impact": evidence.topic.get("has_financial_impact"),
                "requires_authority": evidence.topic.get("requires_authority"),
                "is_irreversible": evidence.topic.get("is_irreversible"),
                "is_sensitive": evidence.topic.get("is_sensitive"),
            }
        }
