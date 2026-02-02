"""
Unit tests for governance gates.
"""

import pytest
from governance_gate.core.types import Intent, Context, Evidence, DecisionAction
from governance_gate.gates import FactVerifiabilityGate, UncertaintyGate, ResponsibilityGate


class TestFactVerifiabilityGate:
    """Tests for FactVerifiabilityGate."""

    def test_name(self):
        gate = FactVerifiabilityGate()
        assert gate.name == "fact_verifiability"

    def test_verifiable_facts_allow(self):
        gate = FactVerifiabilityGate()
        intent = Intent(name="test_intent", confidence=1.0)
        context = Context()
        evidence = Evidence(
            facts={
                "verifiable": True,
                "verifiable_confidence": 0.9,
                "source": "database",
                "freshness": "fresh",
            }
        )

        action, rationale = gate.evaluate(intent, context, evidence)

        assert action is None  # No override
        assert "verifiable" in rationale.lower()

    def test_unverifiable_realtime_facts_restrict(self):
        gate = FactVerifiabilityGate(require_realtime_facts=["test_intent"])
        intent = Intent(name="test_intent", confidence=1.0)
        context = Context()
        evidence = Evidence(
            facts={
                "verifiable": False,
                "verifiable_confidence": 0.3,
                "source": "unknown",
                "freshness": "stale",
                "requires_realtime": True,
            }
        )

        action, rationale = gate.evaluate(intent, context, evidence)

        assert action == DecisionAction.RESTRICT
        assert "real-time" in rationale.lower() or "verifiable" in rationale.lower()

    def test_low_confidence_restrict(self):
        gate = FactVerifiabilityGate(verifiable_threshold=0.7)
        intent = Intent(name="test_intent", confidence=1.0)
        context = Context()
        evidence = Evidence(
            facts={
                "verifiable": True,
                "verifiable_confidence": 0.5,
                "source": "database",
            }
        )

        action, rationale = gate.evaluate(intent, context, evidence)

        # Should not restrict since no realtime requirement
        assert action is None
        assert "confidence" in rationale.lower()

    def test_stale_facts_restrict(self):
        gate = FactVerifiabilityGate()
        intent = Intent(name="test_intent", confidence=1.0)
        context = Context()
        evidence = Evidence(
            facts={
                "verifiable": True,
                "source": "database",
                "freshness": "stale",
            }
        )

        action, rationale = gate.evaluate(intent, context, evidence)

        assert action == DecisionAction.RESTRICT
        assert "stale" in rationale.lower()


class TestUncertaintyGate:
    """Tests for UncertaintyGate."""

    def test_name(self):
        gate = UncertaintyGate()
        assert gate.name == "uncertainty"

    def test_high_confidence_allow(self):
        gate = UncertaintyGate(confidence_threshold=0.6)
        intent = Intent(name="test_intent", confidence=1.0)
        context = Context()
        evidence = Evidence(
            rag={
                "confidence": 0.85,
                "source": "vector_db",
                "has_conflicts": False,
                "kb_age_days": 5,
            }
        )

        action, rationale = gate.evaluate(intent, context, evidence)

        assert action is None
        assert "acceptable" in rationale.lower()

    def test_low_confidence_restrict(self):
        gate = UncertaintyGate(confidence_threshold=0.6)
        intent = Intent(name="test_intent", confidence=1.0)
        context = Context()
        evidence = Evidence(
            rag={
                "confidence": 0.4,
                "source": "vector_db",
                "has_conflicts": False,
            }
        )

        action, rationale = gate.evaluate(intent, context, evidence)

        assert action == DecisionAction.RESTRICT
        assert "confidence" in rationale.lower() or "threshold" in rationale.lower()

    def test_conflicting_results_restrict(self):
        gate = UncertaintyGate()
        intent = Intent(name="test_intent", confidence=1.0)
        context = Context()
        evidence = Evidence(
            rag={
                "confidence": 0.8,
                "has_conflicts": True,
                "conflict_count": 2,
            }
        )

        action, rationale = gate.evaluate(intent, context, evidence)

        assert action == DecisionAction.RESTRICT
        assert "conflict" in rationale.lower()

    def test_outdated_knowledge_restrict(self):
        gate = UncertaintyGate(outdated_version_days=30)
        intent = Intent(name="test_intent", confidence=1.0)
        context = Context()
        evidence = Evidence(
            rag={
                "confidence": 0.8,
                "kb_version": "1.0.0",
                "kb_age_days": 45,
            }
        )

        action, rationale = gate.evaluate(intent, context, evidence)

        assert action == DecisionAction.RESTRICT
        assert "outdated" in rationale.lower() or "old" in rationale.lower()

    def test_tool_disagreement_escalate(self):
        gate = UncertaintyGate()
        intent = Intent(name="test_intent", confidence=1.0)
        context = Context()
        evidence = Evidence(
            rag={
                "confidence": 0.8,
                "tool_disagreement": True,
            }
        )

        action, rationale = gate.evaluate(intent, context, evidence)

        assert action == DecisionAction.ESCALATE
        assert "human" in rationale.lower() or "review" in rationale.lower()


class TestResponsibilityGate:
    """Tests for ResponsibilityGate."""

    def test_name(self):
        gate = ResponsibilityGate()
        assert gate.name == "responsibility"

    def test_within_boundaries_allow(self):
        gate = ResponsibilityGate()
        intent = Intent(name="test_intent", confidence=1.0)
        context = Context()
        evidence = Evidence(
            topic={
                "has_financial_impact": False,
                "requires_authority": False,
                "is_irreversible": False,
                "is_sensitive": False,
            }
        )

        action, rationale = gate.evaluate(intent, context, evidence)

        assert action is None
        assert "boundaries" in rationale.lower()

    def test_financial_impact_escalate(self):
        gate = ResponsibilityGate()
        intent = Intent(name="test_intent", confidence=1.0)
        context = Context()
        evidence = Evidence(
            topic={
                "has_financial_impact": True,
                "requires_authority": False,
                "is_irreversible": False,
                "is_sensitive": False,
            }
        )

        action, rationale = gate.evaluate(intent, context, evidence)

        assert action == DecisionAction.ESCALATE
        assert "financial" in rationale.lower() or "responsibility" in rationale.lower()

    def test_financial_intent_escalate(self):
        gate = ResponsibilityGate()
        intent = Intent(name="refund", confidence=1.0)
        context = Context()
        evidence = Evidence(
            topic={
                "has_financial_impact": False,
                "requires_authority": False,
            }
        )

        action, rationale = gate.evaluate(intent, context, evidence)

        assert action == DecisionAction.ESCALATE
        assert "financial" in rationale.lower()

    def test_authority_required_escalate(self):
        gate = ResponsibilityGate()
        intent = Intent(name="test_intent", confidence=1.0)
        context = Context()
        evidence = Evidence(
            topic={
                "has_financial_impact": False,
                "requires_authority": True,
                "is_irreversible": False,
                "is_sensitive": False,
            }
        )

        action, rationale = gate.evaluate(intent, context, evidence)

        assert action == DecisionAction.ESCALATE
        assert "authority" in rationale.lower() or "commit" in rationale.lower()

    def test_irreversible_escalate(self):
        gate = ResponsibilityGate()
        intent = Intent(name="test_intent", confidence=1.0)
        context = Context()
        evidence = Evidence(
            topic={
                "has_financial_impact": False,
                "requires_authority": False,
                "is_irreversible": True,
                "is_sensitive": False,
            }
        )

        action, rationale = gate.evaluate(intent, context, evidence)

        assert action == DecisionAction.ESCALATE
        assert "irreversible" in rationale.lower() or "approval" in rationale.lower()

    def test_compensation_keywords_escalate(self):
        gate = ResponsibilityGate()
        intent = Intent(
            name="test_intent",
            confidence=1.0,
            parameters={"user_input": "You should compensate me for this issue"},
        )
        context = Context()
        evidence = Evidence(
            topic={
                "has_financial_impact": False,
                "requires_authority": False,
            }
        )

        action, rationale = gate.evaluate(intent, context, evidence)

        assert action == DecisionAction.ESCALATE
        assert "compensat" in rationale.lower() or "financial" in rationale.lower()
