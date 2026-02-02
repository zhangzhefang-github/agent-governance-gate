"""
End-to-end tests for Case Law library.

Tests verify that each failure-mode case produces the expected governance decision.
"""

import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../src"))

import pytest
from governance_gate.core.types import Intent, Context, Evidence, DecisionAction
from governance_gate.core.pipeline import GovernancePipeline
from governance_gate.gates import FactVerifiabilityGate, UncertaintyGate, ResponsibilityGate, SafetyGate


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def governance_pipeline():
    """Create a governance pipeline with all gates including safety."""
    return GovernancePipeline(
        gates=[
            SafetyGate(),
            FactVerifiabilityGate(),
            UncertaintyGate(),
            ResponsibilityGate(),
        ]
    )


@pytest.fixture
def case_law_dir():
    """Get the case law directory."""
    return Path(__file__).parent.parent / "cases"


def load_case(case_dir: Path):
    """Load case input and expected output."""
    input_file = case_dir / "input.json"
    expected_file = case_dir / "expected.json"

    with open(input_file) as f:
        input_data = json.load(f)

    with open(expected_file) as f:
        expected_data = json.load(f)

    return input_data, expected_data


def evaluate_case(input_data, pipeline):
    """Evaluate a case through the governance pipeline."""
    # Build Intent
    intent_data = input_data["intent"]
    intent = Intent(
        name=intent_data["name"],
        confidence=intent_data.get("confidence", 1.0),
        parameters=intent_data.get("parameters", {}),
    )

    # Build Context
    context_data = input_data["context"]
    context = Context(
        user_id=context_data.get("user_id"),
        channel=context_data.get("channel"),
        session_id=context_data.get("session_id"),
    )

    # Build Evidence
    evidence_data = input_data["evidence"]
    evidence = Evidence(
        facts=evidence_data.get("facts", {}),
        rag=evidence_data.get("rag", {}),
        topic=evidence_data.get("topic", {}),
        metadata=evidence_data.get("metadata", {}),
    )

    # Evaluate
    return pipeline.evaluate(intent, context, evidence)


# ============================================================================
# Case 001: Unverifiable Facts
# ============================================================================

def test_case_001_unverifiable_facts(governance_pipeline, case_law_dir):
    """Case 001: Unverifiable facts should result in RESTRICT."""
    input_data, expected_data = load_case(case_law_dir / "001_unverifiable_facts")

    decision = evaluate_case(input_data, governance_pipeline)

    assert decision.action == DecisionAction.RESTRICT
    assert expected_data["rationale_substring"].lower() in decision.rationale.lower()


# ============================================================================
# Case 002: Outdated Knowledge
# ============================================================================

def test_case_002_outdated_knowledge(governance_pipeline, case_law_dir):
    """Case 002: Outdated knowledge should result in RESTRICT."""
    input_data, expected_data = load_case(case_law_dir / "002_outdated_knowledge")

    decision = evaluate_case(input_data, governance_pipeline)

    assert decision.action == DecisionAction.RESTRICT
    assert expected_data["rationale_substring"].lower() in decision.rationale.lower()


# ============================================================================
# Case 003: Conflicting Retrieval
# ============================================================================

def test_case_003_conflicting_retrieval(governance_pipeline, case_law_dir):
    """Case 003: Conflicting retrieval should result in RESTRICT."""
    input_data, expected_data = load_case(case_law_dir / "003_conflicting_retrieval")

    decision = evaluate_case(input_data, governance_pipeline)

    assert decision.action == DecisionAction.RESTRICT
    assert expected_data["rationale_substring"].lower() in decision.rationale.lower()


# ============================================================================
# Case 004: Low Confidence
# ============================================================================

def test_case_004_low_confidence(governance_pipeline, case_law_dir):
    """Case 004: Low confidence should result in RESTRICT."""
    input_data, expected_data = load_case(case_law_dir / "004_low_confidence")

    decision = evaluate_case(input_data, governance_pipeline)

    assert decision.action == DecisionAction.RESTRICT
    assert expected_data["rationale_substring"].lower() in decision.rationale.lower()


# ============================================================================
# Case 005: Financial Commitment
# ============================================================================

def test_case_005_financial_commitment(governance_pipeline, case_law_dir):
    """Case 005: Financial commitment should result in ESCALATE."""
    input_data, expected_data = load_case(case_law_dir / "005_financial_commitment")

    decision = evaluate_case(input_data, governance_pipeline)

    assert decision.action == DecisionAction.ESCALATE
    assert expected_data["rationale_substring"].lower() in decision.rationale.lower()


# ============================================================================
# Case 006: Authority Exceeded
# ============================================================================

def test_case_006_authority_exceeded(governance_pipeline, case_law_dir):
    """Case 006: Authority exceeded should result in ESCALATE."""
    input_data, expected_data = load_case(case_law_dir / "006_authority_exceeded")

    decision = evaluate_case(input_data, governance_pipeline)

    assert decision.action == DecisionAction.ESCALATE
    assert expected_data["rationale_substring"].lower() in decision.rationale.lower()


# ============================================================================
# Case 007: Irreversible Action
# ============================================================================

def test_case_007_irreversible_action(governance_pipeline, case_law_dir):
    """Case 007: Irreversible action should result in ESCALATE."""
    input_data, expected_data = load_case(case_law_dir / "007_irreversible_action")

    decision = evaluate_case(input_data, governance_pipeline)

    assert decision.action == DecisionAction.ESCALATE
    assert expected_data["rationale_substring"].lower() in decision.rationale.lower()


# ============================================================================
# Case 008: Sensitive Topic
# ============================================================================

def test_case_008_sensitive_topic(governance_pipeline, case_law_dir):
    """Case 008: Sensitive topic should result in ESCALATE."""
    input_data, expected_data = load_case(case_law_dir / "008_sensitive_topic")

    decision = evaluate_case(input_data, governance_pipeline)

    assert decision.action == DecisionAction.ESCALATE
    assert expected_data["rationale_substring"].lower() in decision.rationale.lower()


# ============================================================================
# Case 009: Regulatory Compliance
# ============================================================================

def test_case_009_regulatory_compliance(governance_pipeline, case_law_dir):
    """Case 009: Regulatory compliance should result in ESCALATE."""
    input_data, expected_data = load_case(case_law_dir / "009_regulatory_compliance")

    decision = evaluate_case(input_data, governance_pipeline)

    assert decision.action == DecisionAction.ESCALATE
    assert expected_data["rationale_substring"].lower() in decision.rationale.lower()


# ============================================================================
# Case 010: Harmful Content
# ============================================================================

def test_case_010_harmful_content(governance_pipeline, case_law_dir):
    """Case 010: Harmful content should result in ESCALATE."""
    input_data, expected_data = load_case(case_law_dir / "010_harmful_content")

    decision = evaluate_case(input_data, governance_pipeline)

    assert decision.action == DecisionAction.ESCALATE
    assert expected_data["rationale_substring"].lower() in decision.rationale.lower()


# ============================================================================
# Case 011: Fraud Detection (STOP)
# ============================================================================

def test_case_011_fraud_detection(governance_pipeline, case_law_dir):
    """Case 011: Fraud detection should result in STOP."""
    input_data, expected_data = load_case(case_law_dir / "011_fraud_detection")

    decision = evaluate_case(input_data, governance_pipeline)

    assert decision.action == DecisionAction.STOP
    assert expected_data["rationale_substring"].lower() in decision.rationale.lower()
    assert decision.decision_code is not None
    assert "SAFETY_STOP" in decision.decision_code


# ============================================================================
# Case 012: Restricted Content (STOP)
# ============================================================================

def test_case_012_restricted_content(governance_pipeline, case_law_dir):
    """Case 012: Restricted content should result in STOP."""
    input_data, expected_data = load_case(case_law_dir / "012_restricted_content")

    decision = evaluate_case(input_data, governance_pipeline)

    assert decision.action == DecisionAction.STOP
    assert expected_data["rationale_substring"].lower() in decision.rationale.lower()
    assert decision.decision_code is not None
    assert "SAFETY_STOP" in decision.decision_code


# ============================================================================
# Meta Tests: Decision Distribution
# ============================================================================

def test_decision_distribution(governance_pipeline, case_law_dir):
    """Verify the distribution of decisions across all cases."""
    case_dirs = sorted(case_law_dir.glob("*/"))
    case_dirs = [d for d in case_dirs if d.is_dir() and (d / "input.json").exists()]

    decisions = {}

    for case_dir in case_dirs:
        case_name = case_dir.name
        input_data, _ = load_case(case_dir)
        decision = evaluate_case(input_data, governance_pipeline)

        decisions[case_name] = decision.action

    # Verify distribution
    action_counts = {
        DecisionAction.RESTRICT: 0,
        DecisionAction.ESCALATE: 0,
        DecisionAction.STOP: 0,
        DecisionAction.ALLOW: 0,
    }

    for action in decisions.values():
        action_counts[action] += 1

    # We expect:
    # 4 RESTRICT (001, 002, 003, 004)
    # 6 ESCALATE (005, 006, 007, 008, 009, 010)
    # 2 STOP (011, 012)
    assert action_counts[DecisionAction.RESTRICT] == 4
    assert action_counts[DecisionAction.ESCALATE] == 6
    assert action_counts[DecisionAction.STOP] == 2


# ============================================================================
# Meta Tests: Determinism
# ============================================================================

def test_all_cases_are_deterministic(governance_pipeline, case_law_dir):
    """Verify that each case produces the same decision when run multiple times."""
    case_dirs = sorted(case_law_dir.glob("*/"))
    case_dirs = [d for d in case_dirs if d.is_dir() and (d / "input.json").exists()]

    for case_dir in case_dirs:
        input_data, expected_data = load_case(case_dir)

        # Run the same case 3 times
        decisions = []
        for _ in range(3):
            decision = evaluate_case(input_data, governance_pipeline)
            decisions.append(decision.action)

        # All decisions should be identical
        assert len(set(decisions)) == 1, f"Case {case_dir.name} is not deterministic"


# ============================================================================
# Meta Tests: Trace ID Uniqueness
# ============================================================================

def test_all_cases_have_unique_trace_ids(governance_pipeline, case_law_dir):
    """Verify that each evaluation produces a unique trace ID."""
    case_dirs = sorted(case_law_dir.glob("*/"))
    case_dirs = [d for d in case_dirs if d.is_dir() and (d / "input.json").exists()]

    trace_ids = []

    for case_dir in case_dirs:
        input_data, _ = load_case(case_dir)

        decision = evaluate_case(input_data, governance_pipeline)
        trace_ids.append(decision.trace_id)

    # All trace IDs should be unique
    assert len(trace_ids) == len(set(trace_ids)), "Trace IDs are not unique"


# ============================================================================
# Meta Tests: Rationale Presence
# ============================================================================

def test_all_cases_have_rationale(governance_pipeline, case_law_dir):
    """Verify that each case produces a rationale."""
    case_dirs = sorted(case_law_dir.glob("*/"))
    case_dirs = [d for d in case_dirs if d.is_dir() and (d / "input.json").exists()]

    for case_dir in case_dirs:
        input_data, _ = load_case(case_dir)

        decision = evaluate_case(input_data, governance_pipeline)

        assert decision.rationale, f"Case {case_dir.name} has no rationale"
        assert len(decision.rationale) > 0, f"Case {case_dir.name} has empty rationale"
        assert decision.trace_id, f"Case {case_dir.name} has no trace ID"


# ============================================================================
# Meta Tests: Gate Contributions
# ============================================================================

def test_all_cases_have_gate_contributions(governance_pipeline, case_law_dir):
    """Verify that each case has contributions from all gates."""
    case_dirs = sorted(case_law_dir.glob("*/"))
    case_dirs = [d for d in case_dirs if d.is_dir() and (d / "input.json").exists()]

    for case_dir in case_dirs:
        input_data, _ = load_case(case_dir)

        decision = evaluate_case(input_data, governance_pipeline)

        # All 4 gates should contribute (including safety)
        assert "fact_verifiability" in decision.gate_contributions
        assert "uncertainty" in decision.gate_contributions
        assert "responsibility" in decision.gate_contributions
        assert "safety" in decision.gate_contributions


# ============================================================================
# Meta Tests: Final Gate Authority (Structural Enhancement)
# ============================================================================

def test_final_gate_correctness(governance_pipeline, case_law_dir):
    """Verify that final_gate correctly identifies the deciding gate for all cases."""
    case_dirs = sorted(case_law_dir.glob("*/"))
    case_dirs = [d for d in case_dirs if d.is_dir() and (d / "input.json").exists()]

    final_gate_mappings = {
        "001_unverifiable_facts": "fact_verifiability",
        "002_outdated_knowledge": "fact_verifiability",
        "003_conflicting_retrieval": "uncertainty",
        "004_low_confidence": "uncertainty",
        "005_financial_commitment": "responsibility",
        "006_authority_exceeded": "responsibility",
        "007_irreversible_action": "responsibility",
        "008_sensitive_topic": "responsibility",
        "009_regulatory_compliance": "responsibility",
        "010_harmful_content": "responsibility",
        "011_fraud_detection": "safety",
        "012_restricted_content": "safety",
    }

    for case_dir in case_dirs:
        case_name = case_dir.name
        input_data, _ = load_case(case_dir)
        decision = evaluate_case(input_data, governance_pipeline)

        # Verify final_gate is set correctly
        expected_gate = final_gate_mappings.get(case_name)
        if expected_gate:
            assert decision.final_gate == expected_gate, (
                f"Case {case_name}: expected final_gate='{expected_gate}', "
                f"got '{decision.final_gate}' (action={decision.action.value})"
            )


def test_final_gate_semantics(governance_pipeline, case_law_dir):
    """Verify final_gate semantics: None for ALLOW, set for all other actions."""
    case_dirs = sorted(case_law_dir.glob("*/"))
    case_dirs = [d for d in case_dirs if d.is_dir() and (d / "input.json").exists()]

    for case_dir in case_dirs:
        input_data, _ = load_case(case_dir)
        decision = evaluate_case(input_data, governance_pipeline)

        if decision.action == DecisionAction.ALLOW:
            assert decision.final_gate is None, (
                f"Case {case_dir.name}: ALLOW decisions should have final_gate=None"
            )
        else:
            assert decision.final_gate is not None, (
                f"Case {case_dir.name}: {decision.action.value} decisions must have final_gate set"
            )
            assert decision.final_gate in [
                "safety", "responsibility", "fact_verifiability", "uncertainty"
            ], f"Case {case_dir.name}: invalid final_gate '{decision.final_gate}'"


def test_stop_cases_have_safety_gate(governance_pipeline, case_law_dir):
    """Verify all STOP cases have final_gate='safety'."""
    stop_cases = [
        "011_fraud_detection",
        "012_restricted_content",
    ]

    for case_name in stop_cases:
        case_dir = case_law_dir / case_name
        input_data, _ = load_case(case_dir)
        decision = evaluate_case(input_data, governance_pipeline)

        assert decision.action == DecisionAction.STOP
        assert decision.final_gate == "safety", (
            f"Case {case_name}: STOP decisions must have final_gate='safety', "
            f"got '{decision.final_gate}'"
        )


def test_escalate_cases_have_responsibility_gate(governance_pipeline, case_law_dir):
    """Verify all ESCALATE cases have final_gate='responsibility'."""
    escalate_cases = [
        "005_financial_commitment",
        "006_authority_exceeded",
        "007_irreversible_action",
        "008_sensitive_topic",
        "009_regulatory_compliance",
        "010_harmful_content",
    ]

    for case_name in escalate_cases:
        case_dir = case_law_dir / case_name
        input_data, _ = load_case(case_dir)
        decision = evaluate_case(input_data, governance_pipeline)

        assert decision.action == DecisionAction.ESCALATE
        assert decision.final_gate == "responsibility", (
            f"Case {case_name}: ESCALATE decisions must have final_gate='responsibility', "
            f"got '{decision.final_gate}'"
        )
