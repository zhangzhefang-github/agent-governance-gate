"""
Gate that evaluates extreme safety and security risks.

This gate handles the most severe cases that should result in STOP decisions:
- Fraud and payment bypass attempts
- Illegal content requests
- Security attacks
- Harmful/dangerous requests

These cases should immediately STOP execution and refuse the request.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from governance_gate.core.types import Intent, Context, Evidence, DecisionAction
    from governance_gate.core.pipeline import Gate
    from governance_gate.policy.evaluator import PolicyEvaluator

from governance_gate.core.pipeline import Gate
from governance_gate.core.types import DecisionAction


# Keywords and patterns that trigger STOP
FRAUD_KEYWORDS = [
    "bypass",
    "credit card generator",
    "card number generator",
    "cvv generator",
    "fake payment",
    "payment fraud",
    "chargeback fraud",
    "refund fraud",
    "free credit",
    "steal payment",
    "hack payment",
    "payment system",
    "get services for free",
]

ILLEGAL_CONTENT_KEYWORDS = [
    "make bomb",
    "how to make explosive",
    "drug manufacturing",
    "synthetic drug",
    "illegal drug",
    "weapon manufactur",
    "fake id",
    "fake identification",
    "identity theft",
    "money launder",
    "without showing id",
    "without id",
    "buy cigarettes",
    "age restricted",
]

SECURITY_ATTACK_KEYWORDS = [
    "sql injection",
    "xss attack",
    "ddos attack",
    "hack into",
    "exploit vulnerability",
    "brute force",
    "inject code",
]


class SafetyGate(Gate):
    """
    Evaluates extreme safety and security risks.

    Rules:
    - If fraud/payment bypass detected -> STOP
    - If illegal content requested -> STOP
    - If security attack detected -> STOP
    - If harmful/dangerous request -> STOP

    Configuration (via policy):
    - additional_fraud_keywords: Extra fraud keywords to watch for
    - additional_illegal_keywords: Extra illegal content keywords
    - stop_on_sensitive_stop: Whether to use STOP for sensitive topics (default: False)
    """

    name = "safety"

    def __init__(
        self,
        additional_fraud_keywords: list[str] | None = None,
        additional_illegal_keywords: list[str] | None = None,
        stop_on_sensitive_stop: bool = False,
    ) -> None:
        """
        Initialize the safety gate.

        Args:
            additional_fraud_keywords: Additional fraud keywords to detect
            additional_illegal_keywords: Additional illegal content keywords to detect
            stop_on_sensitive_stop: Whether to STOP on sensitive topics (extreme cases only)
        """
        self.fraud_keywords = set(FRAUD_KEYWORDS + (additional_fraud_keywords or []))
        self.illegal_keywords = set(ILLEGAL_CONTENT_KEYWORDS + (additional_illegal_keywords or []))
        self.security_keywords = set(SECURITY_ATTACK_KEYWORDS)
        self.stop_on_sensitive_stop = stop_on_sensitive_stop

    def evaluate(
        self,
        intent: "Intent",
        context: "Context",
        evidence: "Evidence",
        policy: "PolicyEvaluator | None" = None,
    ) -> tuple["DecisionAction | None", str]:
        """
        Evaluate safety risks.

        Returns:
            (DecisionAction, rationale) - Action is None if no override needed
        """
        # Check if policy overrides defaults
        if policy:
            policy_config = policy.get_gate_config(self.name)
            if policy_config:
                additional_fraud = policy_config.get("additional_fraud_keywords", [])
                additional_illegal = policy_config.get("additional_illegal_keywords", [])
                self.fraud_keywords.update(additional_fraud)
                self.illegal_keywords.update(additional_illegal)
                self.stop_on_sensitive_stop = policy_config.get(
                    "stop_on_sensitive_stop", self.stop_on_sensitive_stop
                )

        # Get user input for keyword checking
        user_input = intent.parameters.get("user_input", "").lower()

        # Rule 1: Fraud and payment bypass
        for keyword in self.fraud_keywords:
            if keyword in user_input:
                return (
                    DecisionAction.STOP,
                    f"Fraud request detected: '{keyword}' - Refusing to process payment bypass/fraud attempt",
                )

        # Rule 2: Illegal content
        for keyword in self.illegal_keywords:
            if keyword in user_input:
                return (
                    DecisionAction.STOP,
                    f"Illegal content request detected: '{keyword}' - Refusing to provide illegal/information",
                )

        # Rule 3: Security attacks
        for keyword in self.security_keywords:
            if keyword in user_input:
                return (
                    DecisionAction.STOP,
                    f"Security attack detected: '{keyword}' - Refusing to process security request",
                )

        # Rule 4: Check evidence for explicit safety flags
        harm_risk = evidence.get("topic.harm_risk", False)
        if harm_risk is True:
            # Check if it's fraud-related or illegal-related based on intent
            intent_name = intent.name.lower()
            if "fraud" in intent_name or "payment" in intent_name or "bypass" in intent_name:
                return (
                    DecisionAction.STOP,
                    f"Fraud request detected: '{intent.name}' - Refusing to process payment bypass/fraud attempt",
                )
            elif "illegal" in intent_name or "restricted" in intent_name:
                return (
                    DecisionAction.STOP,
                    f"Illegal content request detected: '{intent.name}' - Refusing to provide illegal/restricted information",
                )
            else:
                return (
                    DecisionAction.STOP,
                    "Request flagged as high-risk/harmful - Refusing to process",
                )

        # Rule 5: Extreme sensitive topics (only if configured)
        if self.stop_on_sensitive_stop:
            is_sensitive = evidence.get("topic.is_sensitive", False)
            if is_sensitive:
                return (
                    DecisionAction.STOP,
                    f"Sensitive topic with stop flag - Intent '{intent.name}' requires human specialist",
                )

        # No safety issues found
        return (
            None,
            f"No safety risks detected for intent '{intent.name}'",
        )

    def get_config_snapshot(self) -> dict[str, Any]:
        """Get the configuration snapshot of this gate."""
        return {
            "fraud_keywords_count": len(self.fraud_keywords),
            "illegal_keywords_count": len(self.illegal_keywords),
            "security_keywords_count": len(self.security_keywords),
            "stop_on_sensitive_stop": self.stop_on_sensitive_stop,
        }

    def get_input_summary(self, evidence: "Evidence") -> dict[str, Any]:
        """Get the input summary (evidence slice) that this gate examined."""
        # Safety gate examines user input and topic flags
        return {
            "user_input": "<redacted_for_privacy>",
            "topic_flags": {
                "harm_risk": evidence.topic.get("harm_risk"),
                "is_sensitive": evidence.topic.get("is_sensitive"),
            },
        }
