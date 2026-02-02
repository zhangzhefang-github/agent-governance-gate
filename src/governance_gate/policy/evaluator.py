"""
Policy evaluator that matches conditions against context.
"""

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from governance_gate.core.types import Intent, Context, Evidence, DecisionAction

from governance_gate.core.types import DecisionAction


class PolicyEvaluator:
    """
    Evaluates policy rules against intent, context, and evidence.

    Rules are evaluated in order (by priority if specified).
    The first matching rule determines the action.
    """

    def __init__(self, policy: dict[str, Any]) -> None:
        """
        Initialize the policy evaluator.

        Args:
            policy: The validated policy dictionary
        """
        self.policy = policy
        self._rules: list[dict[str, Any]] = []
        self._load_rules()

    def _load_rules(self) -> None:
        """Load and sort rules by priority."""
        rules = self.policy.get("rules", [])

        # Filter out disabled rules
        enabled_rules = [r for r in rules if r.get("enabled", True)]

        # Sort by priority (higher priority first), then by order in file
        self._rules = sorted(
            enabled_rules,
            key=lambda r: (-r.get("priority", 0), enabled_rules.index(r)),
        )

    def evaluate(
        self,
        intent: "Intent",
        context: "Context",
        evidence: "Evidence",
    ) -> tuple["DecisionAction | None", str]:
        """
        Evaluate rules against the given context.

        Returns:
            A tuple of (action, rationale):
            - action: The action from the first matching rule, or None if no match
            - rationale: The reason from the matching rule
        """
        # Build context dictionary for condition evaluation
        eval_context = {
            "intent": {
                "name": intent.name,
                "confidence": intent.confidence,
                "parameters": intent.parameters,
            },
            "context": {
                "user_id": context.user_id,
                "channel": context.channel,
                "session_id": context.session_id,
                **context.metadata,
            },
            "evidence": {
                "facts": evidence.facts,
                "rag": evidence.rag,
                "topic": evidence.topic,
                "metadata": evidence.metadata,
            },
        }

        # Evaluate each rule in order
        for rule in self._rules:
            if self._matches_rule(rule, eval_context):
                action = DecisionAction(rule["action"])
                reason = rule.get("reason", f"Matched rule: {rule['name']}")
                return action, reason

        # No rules matched
        return None, "No policy rules matched"

    def _matches_rule(self, rule: dict[str, Any], eval_context: dict[str, Any]) -> bool:
        """Check if a rule's conditions match the context."""
        conditions = rule.get("conditions", {})

        # All conditions must be satisfied (AND logic)
        for field_path, condition in conditions.items():
            if not self._matches_condition(field_path, condition, eval_context):
                return False

        return True

    def _matches_condition(
        self, field_path: str, condition: dict[str, Any], eval_context: dict[str, Any]
    ) -> bool:
        """Check if a single condition matches."""
        # Get the value at the field path
        value = self._get_value(field_path, eval_context)

        # Check each operator in the condition
        for operator, expected in condition.items():
            if not self._apply_operator(operator, value, expected):
                return False

        return True

    def _get_value(self, path: str, context: dict[str, Any]) -> Any:
        """Get a value from context using dotted path notation."""
        parts = path.split(".")
        current: Any = context

        for part in parts:
            if isinstance(current, dict):
                if part not in current:
                    return None
                current = current[part]
            elif hasattr(current, part):
                current = getattr(current, part)
            else:
                return None

        return current

    def _apply_operator(self, operator: str, value: Any, expected: Any) -> bool:
        """Apply a comparison operator."""
        if operator == "equals":
            return value == expected

        elif operator == "not_equals":
            return value != expected

        elif operator == "in":
            return value in expected if isinstance(expected, list) else False

        elif operator == "not_in":
            return value not in expected if isinstance(expected, list) else True

        elif operator == "contains":
            if isinstance(value, str) and isinstance(expected, str):
                return expected in value
            elif isinstance(value, list) and isinstance(expected, (str, int, float)):
                return expected in value
            return False

        elif operator == "not_contains":
            return not self._apply_operator("contains", value, expected)

        elif operator == "any_of":
            if isinstance(value, list) and isinstance(expected, list):
                return any(item in expected for item in value)
            return value in expected if isinstance(expected, list) else False

        elif operator == "all_of":
            if isinstance(value, list) and isinstance(expected, list):
                return all(item in expected for item in value)
            return value in expected if isinstance(expected, list) else False

        elif operator == "gt":
            return isinstance(value, (int, float)) and value > expected

        elif operator == "gte":
            return isinstance(value, (int, float)) and value >= expected

        elif operator == "lt":
            return isinstance(value, (int, float)) and value < expected

        elif operator == "lte":
            return isinstance(value, (int, float)) and value <= expected

        elif operator == "between":
            if isinstance(value, (int, float)) and isinstance(expected, list) and len(expected) == 2:
                return expected[0] <= value <= expected[1]
            return False

        elif operator == "is_true":
            return value is True

        elif operator == "is_false":
            return value is False

        elif operator == "is_null":
            return value is None

        elif operator == "is_not_null":
            return value is not None

        elif operator == "matches":
            import re
            if isinstance(value, str) and isinstance(expected, str):
                try:
                    return bool(re.search(expected, value))
                except re.error:
                    return False
            return False

        elif operator == "starts_with":
            if isinstance(value, str) and isinstance(expected, str):
                return value.startswith(expected)
            return False

        elif operator == "ends_with":
            if isinstance(value, str) and isinstance(expected, str):
                return value.endswith(expected)
            return False

        else:
            # Unknown operator - fail safely
            return False

    def get_gate_config(self, gate_name: str) -> dict[str, Any]:
        """
        Get configuration for a specific gate.

        Args:
            gate_name: Name of the gate

        Returns:
            Gate configuration dictionary
        """
        gates = self.policy.get("gates", {})
        return gates.get(gate_name, {})
