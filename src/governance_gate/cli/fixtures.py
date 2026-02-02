"""
Fixtures for testing and CLI usage.
"""

from governance_gate.core.types import Intent, Context, Evidence, DecisionAction


# Sample intent for testing
SAMPLE_INTENT = Intent(
    name="order_status_query",
    confidence=0.95,
    parameters={"order_id": "12345", "user_input": "Where is my order?"},
)

# Sample context for testing
SAMPLE_CONTEXT = Context(
    user_id="user_123",
    channel="web",
    session_id="session_456",
)

# Sample evidence for testing (ALLOW case)
SAMPLE_EVIDENCE_ALLOW = Evidence(
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
        "kb_version": "1.2.3",
        "kb_age_days": 5,
        "coverage": 0.95,
    },
    topic={
        "has_financial_impact": False,
        "requires_authority": False,
        "is_irreversible": False,
        "is_sensitive": False,
    },
)

# Sample evidence for testing (RESTRICT case)
SAMPLE_EVIDENCE_RESTRICT = Evidence(
    facts={
        "verifiable": False,
        "verifiable_confidence": 0.3,
        "source": "unknown",
        "freshness": "stale",
        "requires_realtime": True,
    },
    rag={
        "confidence": 0.85,
        "source": "vector_db",
        "has_conflicts": False,
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

# Sample evidence for testing (ESCALATE case)
SAMPLE_EVIDENCE_ESCALATE = Evidence(
    facts={
        "verifiable": True,
        "verifiable_confidence": 0.9,
        "source": "database",
        "freshness": "fresh",
    },
    rag={
        "confidence": 0.85,
        "source": "vector_db",
        "has_conflicts": False,
    },
    topic={
        "has_financial_impact": True,
        "requires_authority": False,
        "is_irreversible": False,
        "is_sensitive": False,
    },
)
