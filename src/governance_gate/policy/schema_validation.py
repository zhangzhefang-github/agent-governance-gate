"""
Policy schema validation.

Validates the structure and content of policy files.
"""

from typing import Any


# Expected policy structure
REQUIRED_TOP_LEVEL_KEYS = ["version", "name", "rules"]
OPTIONAL_TOP_LEVEL_KEYS = ["description", "gates", "metadata"]

REQUIRED_RULE_KEYS = ["name", "conditions", "action"]
OPTIONAL_RULE_KEYS = ["reason", "enabled", "priority"]

SUPPORTED_OPERATORS = {
    # Equality operators
    "equals",
    "not_equals",
    "in",
    "not_in",
    "contains",
    "not_contains",
    "any_of",
    "all_of",
    # Numeric operators
    "gt",
    "gte",
    "lt",
    "lte",
    "between",
    # Boolean operators
    "is_true",
    "is_false",
    "is_null",
    "is_not_null",
    # Pattern operators
    "matches",
    "starts_with",
    "ends_with",
}

SUPPORTED_ACTIONS = {"ALLOW", "RESTRICT", "ESCALATE", "STOP"}


class PolicyValidationError(Exception):
    """Raised when policy validation fails."""

    def __init__(self, message: str, path: str = ""):
        self.message = message
        self.path = path
        super().__init__(f"{path}: {message}" if path else message)


def validate_policy_schema(policy: dict[str, Any]) -> list[str]:
    """
    Validate the policy schema and return a list of errors.

    Args:
        policy: The policy dictionary to validate

    Returns:
        A list of error messages (empty if valid)

    Raises:
        PolicyValidationError: If a critical validation error is found
    """
    errors = []

    # Validate top-level structure
    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in policy:
            errors.append(f"Missing required top-level key: {key}")

    # Validate version
    if "version" in policy:
        if not isinstance(policy["version"], str):
            errors.append("Policy version must be a string")
        elif not policy["version"].startswith("1."):
            errors.append(f"Unsupported policy version: {policy['version']} (only 1.x supported)")

    # Validate name
    if "name" in policy:
        if not isinstance(policy["name"], str) or not policy["name"].strip():
            errors.append("Policy name must be a non-empty string")

    # Validate rules
    if "rules" in policy:
        if not isinstance(policy["rules"], list):
            errors.append("Policy 'rules' must be a list")
        else:
            for i, rule in enumerate(policy["rules"]):
                rule_errors = _validate_rule(rule, f"rules[{i}]")
                errors.extend(rule_errors)

    # Validate gates configuration
    if "gates" in policy:
        if not isinstance(policy["gates"], dict):
            errors.append("Policy 'gates' must be a dictionary")
        else:
            for gate_name, gate_config in policy["gates"].items():
                if not isinstance(gate_config, dict):
                    errors.append(f"Gate config for '{gate_name}' must be a dictionary")

    if errors:
        raise PolicyValidationError(f"Policy validation failed with {len(errors)} error(s)")

    return []


def _validate_rule(rule: dict[str, Any], path: str) -> list[str]:
    """Validate a single rule."""
    errors = []

    # Check required keys
    for key in REQUIRED_RULE_KEYS:
        if key not in rule:
            errors.append(f"{path}: Missing required key '{key}'")

    # Validate name
    if "name" in rule:
        if not isinstance(rule["name"], str) or not rule["name"].strip():
            errors.append(f"{path}: Rule name must be a non-empty string")

    # Validate action
    if "action" in rule:
        if rule["action"] not in SUPPORTED_ACTIONS:
            errors.append(
                f"{path}: Invalid action '{rule['action']}'. Must be one of: {SUPPORTED_ACTIONS}"
            )

    # Validate conditions
    if "conditions" in rule:
        if not isinstance(rule["conditions"], dict):
            errors.append(f"{path}: Conditions must be a dictionary")
        else:
            condition_errors = _validate_conditions(rule["conditions"], f"{path}.conditions")
            errors.extend(condition_errors)

    # Validate optional fields
    if "enabled" in rule and not isinstance(rule["enabled"], bool):
        errors.append(f"{path}: 'enabled' must be a boolean")

    if "priority" in rule:
        if not isinstance(rule["priority"], int) or rule["priority"] < 0:
            errors.append(f"{path}: 'priority' must be a non-negative integer")

    return errors


def _validate_conditions(conditions: dict[str, Any], path: str) -> list[str]:
    """Validate conditions dictionary."""
    errors = []

    for field_path, condition in conditions.items():
        if not isinstance(condition, dict):
            errors.append(f"{path}.{field_path}: Condition must be a dictionary")
            continue

        for operator, value in condition.items():
            if operator not in SUPPORTED_OPERATORS:
                errors.append(
                    f"{path}.{field_path}: Unsupported operator '{operator}'. "
                    f"Supported: {sorted(SUPPORTED_OPERATORS)}"
                )

            # Validate operator-specific value types
            if operator in {"gt", "gte", "lt", "lte", "between"}:
                if not isinstance(value, (int, float)):
                    errors.append(
                        f"{path}.{field_path}: Operator '{operator}' requires numeric value"
                    )

            elif operator in {"in", "not_in", "any_of", "all_of"}:
                if not isinstance(value, list):
                    errors.append(
                        f"{path}.{field_path}: Operator '{operator}' requires list value"
                    )

            elif operator in {"is_true", "is_false", "is_null", "is_not_null"}:
                if value is not True and value is not False:
                    errors.append(
                        f"{path}.{field_path}: Operator '{operator}' value must be true or false"
                    )

    return errors
