"""
Policy loader for reading YAML policy files.
"""

from pathlib import Path
from typing import Any
import yaml

from governance_gate.policy.schema_validation import validate_policy_schema, PolicyValidationError
from governance_gate.core.errors import PolicyError


class PolicyLoader:
    """
    Loads and validates policy files from YAML.

    The policy file defines:
    - Rules that map conditions to actions
    - Gate configurations
    - Metadata
    """

    def __init__(self, policy_path: str | Path) -> None:
        """
        Initialize the policy loader.

        Args:
            policy_path: Path to the YAML policy file
        """
        self.policy_path = Path(policy_path)
        self._policy: dict[str, Any] | None = None

    def load(self) -> dict[str, Any]:
        """
        Load and validate the policy file.

        Returns:
            The validated policy dictionary

        Raises:
            PolicyError: If the file cannot be loaded or validation fails
        """
        if not self.policy_path.exists():
            raise PolicyError(f"Policy file not found: {self.policy_path}")

        try:
            with open(self.policy_path, "r") as f:
                policy = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise PolicyError(f"Failed to parse YAML file {self.policy_path}: {e}")
        except Exception as e:
            raise PolicyError(f"Failed to read policy file {self.policy_path}: {e}")

        if not isinstance(policy, dict):
            raise PolicyError(f"Policy file must contain a dictionary, got {type(policy).__name__}")

        # Validate the policy structure
        try:
            validate_policy_schema(policy)
        except PolicyValidationError as e:
            raise PolicyError(f"Policy validation failed: {e}")

        self._policy = policy
        return policy

    @property
    def policy(self) -> dict[str, Any]:
        """Get the loaded policy (loads if not already loaded)."""
        if self._policy is None:
            self.load()
        return self._policy

    def get_rules(self) -> list[dict[str, Any]]:
        """Get all rules from the policy."""
        return self.policy.get("rules", [])

    def get_gate_config(self, gate_name: str) -> dict[str, Any]:
        """
        Get configuration for a specific gate.

        Args:
            gate_name: Name of the gate (e.g., "fact_verifiability")

        Returns:
            Gate configuration dictionary, or empty dict if not found
        """
        gates = self.policy.get("gates", {})
        return gates.get(gate_name, {})

    def get_metadata(self) -> dict[str, Any]:
        """Get policy metadata."""
        return self.policy.get("metadata", {})

    @staticmethod
    def load_from_string(yaml_content: str) -> dict[str, Any]:
        """
        Load a policy from a YAML string.

        Args:
            yaml_content: YAML content as a string

        Returns:
            The validated policy dictionary

        Raises:
            PolicyError: If parsing or validation fails
        """
        try:
            policy = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise PolicyError(f"Failed to parse YAML content: {e}")

        if not isinstance(policy, dict):
            raise PolicyError(f"Policy must contain a dictionary, got {type(policy).__name__}")

        try:
            validate_policy_schema(policy)
        except PolicyValidationError as e:
            raise PolicyError(f"Policy validation failed: {e}")

        return policy
