"""
Pytest fixtures and configuration.
"""

import pytest
from governance_gate.core.types import Intent, Context, Evidence, DecisionAction
from governance_gate.core.pipeline import GovernancePipeline
from governance_gate.gates import FactVerifiabilityGate, UncertaintyGate, ResponsibilityGate
from governance_gate.policy.loader import PolicyLoader
from governance_gate.policy.evaluator import PolicyEvaluator
from pathlib import Path


# Sample intent for testing
@pytest.fixture
def sample_intent():
    return Intent(
        name="order_status_query",
        confidence=0.95,
        parameters={"order_id": "12345"},
    )


# Sample context for testing
@pytest.fixture
def sample_context():
    return Context(
        user_id="user_123",
        channel="web",
        session_id="session_456",
    )


# Evidence for ALLOW case
@pytest.fixture
def evidence_allow():
    return Evidence(
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
            "kb_age_days": 5,
        },
        topic={
            "has_financial_impact": False,
            "requires_authority": False,
            "is_irreversible": False,
            "is_sensitive": False,
        },
    )


# Evidence for RESTRICT case (unverifiable facts)
@pytest.fixture
def evidence_restrict_facts():
    return Evidence(
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
            "kb_age_days": 5,
        },
        topic={
            "has_financial_impact": False,
            "requires_authority": False,
        },
    )


# Evidence for RESTRICT case (low RAG confidence)
@pytest.fixture
def evidence_restrict_rag():
    return Evidence(
        facts={
            "verifiable": True,
            "verifiable_confidence": 0.9,
            "source": "database",
        },
        rag={
            "confidence": 0.4,  # Below threshold
            "source": "vector_db",
            "has_conflicts": False,
            "kb_age_days": 5,
        },
        topic={
            "has_financial_impact": False,
        },
    )


# Evidence for ESCALATE case (financial impact)
@pytest.fixture
def evidence_escalate():
    return Evidence(
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
            "is_irreversible": False,
            "is_sensitive": False,
        },
    )


# Evidence for STOP case (conflicting retrieval)
@pytest.fixture
def evidence_stop():
    return Evidence(
        facts={
            "verifiable": True,
            "source": "database",
        },
        rag={
            "confidence": 0.7,
            "has_conflicts": True,
            "conflict_count": 3,
        },
        topic={
            "has_financial_impact": False,
        },
    )


@pytest.fixture
def sample_pipeline():
    """Create a pipeline with all gates."""
    return GovernancePipeline(
        gates=[
            FactVerifiabilityGate(),
            UncertaintyGate(),
            ResponsibilityGate(),
        ]
    )


@pytest.fixture
def customer_support_policy():
    """Load the customer support policy."""
    policy_path = Path(__file__).parent.parent / "policies" / "presets" / "customer_support.yaml"
    if policy_path.exists():
        loader = PolicyLoader(policy_path)
        policy = loader.load()
        return PolicyEvaluator(policy)
    return None
