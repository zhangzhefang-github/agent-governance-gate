"""
API Configuration for governance gate service.

Environment-based configuration for failure modes and other API-level settings.
"""

import os
from dataclasses import dataclass
from typing import Literal


@dataclass
class APIConfig:
    """Configuration for the governance gate API."""

    # Failure mode: what to do when evaluation fails
    # Options:
    #   - "fail_closed": Return ESCALATE (conservative, safe for production)
    #   - "fail_open": Return RESTRICT with warning (less conservative, testing only)
    failure_mode: Literal["fail_closed", "fail_open"] = "fail_closed"

    # Policy directory
    policy_base_dir: str = os.environ.get(
        "GOVGATE_POLICY_DIR",
        "./policies/presets"
    )

    # Decision timeout (seconds)
    decision_timeout_seconds: float = float(
        os.environ.get("GOVGATE_DECISION_TIMEOUT", "5.0")
    )

    @classmethod
    def from_env(cls) -> "APIConfig":
        """Load configuration from environment variables."""
        failure_mode = os.environ.get("GOVGATE_FAILURE_MODE", "fail_closed")

        if failure_mode not in ["fail_closed", "fail_open"]:
            raise ValueError(
                f"Invalid GOVGATE_FAILURE_MODE: {failure_mode}. "
                "Must be 'fail_closed' or 'fail_open'"
            )

        return cls(
            failure_mode=failure_mode,
            policy_base_dir=cls.policy_base_dir,
            decision_timeout_seconds=cls.decision_timeout_seconds
        )


# Global configuration instance
config = APIConfig.from_env()
