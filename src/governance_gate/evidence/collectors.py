"""
Evidence collectors for gathering information about intent, context, and facts.
"""

from abc import ABC, abstractmethod
from typing import Any
from governance_gate.core.types import Evidence


class EvidenceCollector(ABC):
    """Abstract base class for evidence collectors."""

    @abstractmethod
    def collect(self, intent_data: dict[str, Any], context_data: dict[str, Any]) -> dict[str, Any]:
        """
        Collect evidence from intent and context.

        Args:
            intent_data: Raw intent data
            context_data: Raw context data

        Returns:
            Collected evidence as a dictionary
        """
        pass


class SimpleEvidenceCollector(EvidenceCollector):
    """
    Simple evidence collector that extracts evidence from provided data.

    This collector expects structured input with evidence already organized.
    """

    def collect(self, intent_data: dict[str, Any], context_data: dict[str, Any]) -> dict[str, Any]:
        """Collect evidence from intent and context data."""
        evidence = {
            "facts": context_data.get("facts", {}),
            "rag": context_data.get("rag", {}),
            "topic": context_data.get("topic", {}),
            "metadata": context_data.get("metadata", {}),
        }
        return evidence


def build_evidence(
    intent_data: dict[str, Any],
    context_data: dict[str, Any],
    collector: EvidenceCollector | None = None,
) -> Evidence:
    """
    Build an Evidence object from raw data.

    Args:
        intent_data: Raw intent data
        context_data: Raw context data (should contain facts, rag, topic)
        collector: Optional custom evidence collector

    Returns:
        An Evidence object
    """
    if collector is None:
        collector = SimpleEvidenceCollector()

    evidence_data = collector.collect(intent_data, context_data)

    return Evidence(
        facts=evidence_data.get("facts", {}),
        rag=evidence_data.get("rag", {}),
        topic=evidence_data.get("topic", {}),
        metadata=evidence_data.get("metadata", {}),
    )
