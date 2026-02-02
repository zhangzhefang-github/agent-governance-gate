"""
Integration tests for the governance pipeline.
"""

import pytest
from governance_gate.core.types import Intent, Context, Evidence, DecisionAction
from governance_gate.core.pipeline import GovernancePipeline
from governance_gate.gates import FactVerifiabilityGate, UncertaintyGate, ResponsibilityGate
from governance_gate.policy.loader import PolicyLoader
from governance_gate.policy.evaluator import PolicyEvaluator
from pathlib import Path


class TestGovernancePipeline:
    """Integration tests for the full governance pipeline."""

    def test_pipeline_with_all_gates_allow(self):
        """Test pipeline with all gates passing."""
        pipeline = GovernancePipeline(
            gates=[
                FactVerifiabilityGate(),
                UncertaintyGate(),
                ResponsibilityGate(),
            ]
        )

        intent = Intent(name="test_intent", confidence=0.95)
        context = Context(user_id="user_123", channel="web")
        evidence = Evidence(
            facts={
                "verifiable": True,
                "verifiable_confidence": 0.9,
                "source": "database",
                "freshness": "fresh",
            },
            rag={
                "confidence": 0.85,
                "has_conflicts": False,
                "kb_age_days": 5,
            },
            topic={
                "has_financial_impact": False,
                "requires_authority": False,
                "is_irreversible": False,
            },
        )

        decision = pipeline.evaluate(intent, context, evidence)

        assert decision.action == DecisionAction.ALLOW
        assert decision.trace_id is not None
        assert len(decision.gate_contributions) == 3
        assert "fact_verifiability" in decision.gate_contributions
        assert "uncertainty" in decision.gate_contributions
        assert "responsibility" in decision.gate_contributions
        # ALLOW decisions should have final_gate=None
        assert decision.final_gate is None

    def test_pipeline_restrict_unverifiable_facts(self):
        """Test pipeline with unverifiable facts."""
        pipeline = GovernancePipeline(
            gates=[
                FactVerifiabilityGate(require_realtime_facts=["test_intent"]),
                UncertaintyGate(),
                ResponsibilityGate(),
            ]
        )

        intent = Intent(name="test_intent", confidence=0.95)
        context = Context()
        evidence = Evidence(
            facts={
                "verifiable": False,
                "verifiable_confidence": 0.4,
                "source": "unknown",
                "freshness": "stale",
                "requires_realtime": True,
            },
            rag={
                "confidence": 0.85,
                "has_conflicts": False,
            },
            topic={
                "has_financial_impact": False,
            },
        )

        decision = pipeline.evaluate(intent, context, evidence)

        assert decision.action == DecisionAction.RESTRICT
        assert "verifiable" in decision.rationale.lower() or "real-time" in decision.rationale.lower()
        assert decision.final_gate == "fact_verifiability"

    def test_pipeline_escalate_financial(self):
        """Test pipeline with financial impact."""
        pipeline = GovernancePipeline(
            gates=[
                FactVerifiabilityGate(),
                UncertaintyGate(),
                ResponsibilityGate(),
            ]
        )

        intent = Intent(name="test_intent", confidence=0.95)
        context = Context()
        evidence = Evidence(
            facts={
                "verifiable": True,
                "verifiable_confidence": 0.9,
                "source": "database",
            },
            rag={
                "confidence": 0.85,
                "has_conflicts": False,
            },
            topic={
                "has_financial_impact": True,
                "requires_authority": False,
            },
        )

        decision = pipeline.evaluate(intent, context, evidence)

        assert decision.action == DecisionAction.ESCALATE
        assert "financial" in decision.rationale.lower()
        assert decision.final_gate == "responsibility"

    def test_pipeline_precedence_stop_over_restrict(self):
        """Test that STOP has higher precedence than RESTRICT."""
        pipeline = GovernancePipeline(
            gates=[
                UncertaintyGate(stop_on_conflict=True),  # Will STOP on conflicts
                FactVerifiabilityGate(),  # Would RESTRICT
            ]
        )

        intent = Intent(name="test_intent", confidence=0.95)
        context = Context()
        evidence = Evidence(
            facts={
                "verifiable": False,  # Would trigger RESTRICT
                "verifiable_confidence": 0.3,
            },
            rag={
                "confidence": 0.8,
                "has_conflicts": True,  # Will trigger STOP
                "conflict_count": 2,
            },
            topic={
                "has_financial_impact": False,
            },
        )

        decision = pipeline.evaluate(intent, context, evidence)

        # STOP should win over RESTRICT
        assert decision.action == DecisionAction.STOP
        # UncertaintyGate caused the STOP (due to stop_on_conflict=True)
        assert decision.final_gate == "uncertainty"

    def test_pipeline_precedence_escalate_over_allow(self):
        """Test that ESCALATE has higher precedence than ALLOW."""
        pipeline = GovernancePipeline(
            gates=[
                FactVerifiabilityGate(),  # Would allow
                ResponsibilityGate(),  # Will ESCALATE on financial
            ]
        )

        intent = Intent(name="test_intent", confidence=0.95)
        context = Context()
        evidence = Evidence(
            facts={
                "verifiable": True,
                "verifiable_confidence": 0.9,
            },
            rag={
                "confidence": 0.85,
                "has_conflicts": False,
            },
            topic={
                "has_financial_impact": True,  # Will trigger ESCALATE
            },
        )

        decision = pipeline.evaluate(intent, context, evidence)

        assert decision.action == DecisionAction.ESCALATE

    def test_decision_to_dict(self):
        """Test decision serialization."""
        pipeline = GovernancePipeline(
            gates=[
                FactVerifiabilityGate(),
                UncertaintyGate(),
                ResponsibilityGate(),
            ]
        )

        intent = Intent(name="test_intent", confidence=0.95)
        context = Context()
        evidence = Evidence(
            facts={"verifiable": True, "verifiable_confidence": 0.9},
            rag={"confidence": 0.85, "has_conflicts": False},
            topic={"has_financial_impact": False},
        )

        decision = pipeline.evaluate(intent, context, evidence)
        decision_dict = decision.to_dict()

        assert "action" in decision_dict
        assert "rationale" in decision_dict
        assert "trace_id" in decision_dict
        assert "evidence_summary" in decision_dict
        assert "gate_contributions" in decision_dict
        assert decision_dict["action"] == decision.action.value

    def test_decision_from_dict(self):
        """Test decision deserialization."""
        from governance_gate.core.decision import Decision

        decision_dict = {
            "action": "ALLOW",
            "rationale": "Test rationale",
            "trace_id": "test-trace-id-123",
            "evidence_summary": {"test": "data"},
            "required_steps": [],
            "gate_contributions": {},
        }

        decision = Decision.from_dict(decision_dict)

        assert decision.action == DecisionAction.ALLOW
        assert decision.rationale == "Test rationale"
        assert decision.trace_id == "test-trace-id-123"

    def test_pipeline_with_policy(self, customer_support_policy):
        """Test pipeline with policy evaluator."""
        if not customer_support_policy:
            pytest.skip("Customer support policy not found")

        pipeline = GovernancePipeline(
            gates=[
                FactVerifiabilityGate(),
                UncertaintyGate(),
                ResponsibilityGate(),
            ]
        )

        intent = Intent(
            name="order_status_query",
            confidence=0.95,
            parameters={"user_input": "How do I check my order?"},
        )
        context = Context(channel="web")
        evidence = Evidence(
            facts={"verifiable": True, "verifiable_confidence": 0.9, "requires_realtime": False},
            rag={"confidence": 0.85, "has_conflicts": False},
            topic={"has_financial_impact": False},
        )

        decision = pipeline.evaluate(intent, context, evidence, customer_support_policy)

        # Should be ALLOW based on policy rules
        assert decision.action == DecisionAction.ALLOW


class TestCustomerSupportExamples:
    """Test the customer support example cases."""

    def test_case_01_allow(self, sample_pipeline):
        """Test case 01: ALLOW - rule explanation only."""
        intent = Intent(
            name="order_status_query",
            confidence=0.95,
            parameters={"user_input": "How do I check my order status?"},
        )
        context = Context(user_id="user_123", channel="web")
        evidence = Evidence(
            facts={
                "verifiable": True,
                "verifiable_confidence": 0.9,
                "source": "database",
                "freshness": "fresh",
                "requires_realtime": False,
            },
            rag={
                "confidence": 0.85,
                "source": "vector_db",
                "has_conflicts": False,
                "conflict_count": 0,
                "kb_version": "1.2.3",
                "kb_age_days": 5,
            },
            topic={
                "has_financial_impact": False,
                "requires_authority": False,
                "is_irreversible": False,
                "is_sensitive": False,
            },
        )

        decision = sample_pipeline.evaluate(intent, context, evidence)

        assert decision.action == DecisionAction.ALLOW

    def test_case_02_restrict(self, sample_pipeline):
        """Test case 02: RESTRICT - depends on real-time facts."""
        intent = Intent(
            name="order_status_query",
            confidence=0.92,
            parameters={"user_input": "Why has my order not shipped yet?"},
        )
        context = Context(user_id="user_123", channel="web")
        evidence = Evidence(
            facts={
                "verifiable": False,
                "verifiable_confidence": 0.4,
                "source": "unknown",
                "freshness": "stale",
                "requires_realtime": True,
            },
            rag={
                "confidence": 0.85,
                "source": "vector_db",
                "has_conflicts": False,
                "conflict_count": 0,
                "kb_version": "1.2.3",
                "kb_age_days": 5,
            },
            topic={
                "has_financial_impact": False,
                "requires_authority": False,
                "is_irreversible": False,
                "is_sensitive": False,
            },
        )

        decision = sample_pipeline.evaluate(intent, context, evidence)

        assert decision.action == DecisionAction.RESTRICT
        assert "real-time" in decision.rationale.lower() or "verifiable" in decision.rationale.lower()

    def test_case_03_escalate(self, sample_pipeline):
        """Test case 03: ESCALATE - financial responsibility."""
        intent = Intent(
            name="order_status_query",
            confidence=0.90,
            parameters={"user_input": "You messed up my order, you should compensate me"},
        )
        context = Context(user_id="user_123", channel="web")
        evidence = Evidence(
            facts={
                "verifiable": True,
                "verifiable_confidence": 0.85,
                "source": "database",
                "freshness": "fresh",
                "requires_realtime": False,
            },
            rag={
                "confidence": 0.80,
                "source": "vector_db",
                "has_conflicts": False,
                "conflict_count": 0,
                "kb_version": "1.2.3",
                "kb_age_days": 5,
            },
            topic={
                "has_financial_impact": True,
                "requires_authority": False,
                "is_irreversible": False,
                "is_sensitive": False,
            },
        )

        decision = sample_pipeline.evaluate(intent, context, evidence)

        assert decision.action == DecisionAction.ESCALATE
        assert "financial" in decision.rationale.lower()
