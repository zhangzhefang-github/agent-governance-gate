"""
Evidence normalizers for standardizing evidence formats.
"""

from typing import Any


class EvidenceNormalizer:
    """
    Normalizes evidence values to standard types and ranges.
    """

    @staticmethod
    def normalize_confidence(value: Any, default: float = 1.0) -> float:
        """
        Normalize a confidence value to [0.0, 1.0].

        Args:
            value: The confidence value (can be float, int, or string)
            default: Default value if normalization fails

        Returns:
            Normalized confidence in [0.0, 1.0]
        """
        try:
            if isinstance(value, str):
                value = float(value)
            if not isinstance(value, (int, float)):
                return default

            # Clamp to [0.0, 1.0]
            return max(0.0, min(1.0, float(value)))
        except (ValueError, TypeError):
            return default

    @staticmethod
    def normalize_boolean(value: Any, default: bool = False) -> bool:
        """
        Normalize a value to boolean.

        Args:
            value: The value to normalize
            default: Default value if normalization fails

        Returns:
            Normalized boolean value
        """
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in {"true", "yes", "1", "on"}
        if isinstance(value, (int, float)):
            return value != 0
        return default

    @staticmethod
    def normalize_list(value: Any, default: list | None = None) -> list:
        """
        Normalize a value to a list.

        Args:
            value: The value to normalize
            default: Default value if normalization fails

        Returns:
            Normalized list value
        """
        if isinstance(value, list):
            return value
        if value is None:
            return default or []
        return [value]

    @staticmethod
    def normalize_freshness(value: Any) -> str:
        """
        Normalize a freshness value to standard categories.

        Args:
            value: Freshness value (can be int days, string, or dict)

        Returns:
            Normalized freshness category: "fresh", "stale", "outdated", "unknown"
        """
        if isinstance(value, int):
            # Assume days
            if value < 1:
                return "fresh"
            elif value < 7:
                return "fresh"
            elif value < 30:
                return "stale"
            else:
                return "outdated"

        if isinstance(value, str):
            value_lower = value.lower()
            if value_lower in {"fresh", "recent", "current"}:
                return "fresh"
            elif value_lower in {"stale", "aging", "old"}:
                return "stale"
            elif value_lower in {"outdated", "expired", "obsolete"}:
                return "outdated"
            return "unknown"

        if isinstance(value, dict):
            status = value.get("status", "unknown")
            return str(status).lower()

        return "unknown"
