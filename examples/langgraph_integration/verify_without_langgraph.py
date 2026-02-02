#!/usr/bin/env python3
"""
Verify the LangGraph integration adapter works without installing langgraph.

This script tests the adapter logic (state conversion, decision evaluation, routing)
without actually running a LangGraph graph.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))

from adapter import AgentState, LangGraphGovernanceAdapter, create_customer_support_adapter


def make_state(intent_name: str, verifiable: bool, has_financial: bool) -> AgentState:
    """Create a test state."""
    return {
        "user_input": "Test input",
        "intent_name": intent_name,
        "intent_confidence": 0.9,
        "intent_parameters": {},
        "user_id": "test_user",
        "channel": "test",
        "session_id": "test_session",
        "evidence": {
            "facts": {
                "verifiable": verifiable,
                "verifiable_confidence": 0.9 if verifiable else 0.4,
                "source": "database" if verifiable else "unknown",
                "freshness": "fresh" if verifiable else "stale",
                "requires_realtime": not verifiable,
            },
            "rag": {
                "confidence": 0.85,
                "has_conflicts": False,
                "kb_age_days": 5,
            },
            "topic": {
                "has_financial_impact": has_financial,
                "requires_authority": False,
                "is_irreversible": False,
                "is_sensitive": False,
            },
        },
        "governance_action": None,
        "governance_rationale": None,
        "governance_trace_id": None,
        "tool_result": None,
        "response": None,
    }


def main():
    print("=" * 80)
    print("LangGraph Integration Adapter Verification")
    print("=" * 80)
    print()

    # Create adapter
    print("Creating adapter with customer support policy...")
    adapter = create_customer_support_adapter()
    print("✓ Adapter created")
    print()

    # Test cases matching the example cases
    test_cases = [
        {
            "name": "Case 1: ALLOW",
            "intent": "order_status_query",
            "verifiable": True,
            "financial": False,
            "expected": "ALLOW",
        },
        {
            "name": "Case 2: RESTRICT",
            "intent": "order_status_query",
            "verifiable": False,
            "financial": False,
            "expected": "RESTRICT",
        },
        {
            "name": "Case 3: ESCALATE",
            "intent": "order_status_query",
            "verifiable": True,
            "financial": True,
            "expected": "ESCALATE",
        },
    ]

    all_passed = True

    for test in test_cases:
        print("-" * 80)
        print(f"{test['name']}")
        print("-" * 80)

        # Create state
        state = make_state(test["intent"], test["verifiable"], test["financial"])

        # Evaluate
        result = adapter.evaluate_governance(state)

        # Check result
        actual = result["governance_action"]
        expected = test["expected"]

        passed = actual == expected
        status = "✓ PASS" if passed else "✗ FAIL"

        print(f"Expected: {expected}")
        print(f"Actual:   {actual}")
        print(f"Trace ID: {result.get('governance_trace_id', 'N/A')}")
        print(f"Rationale: {result.get('governance_rationale', 'N/A')[:80]}...")
        print(status)
        print()

        if not passed:
            all_passed = False

    # Test routing
    print("-" * 80)
    print("Routing Tests")
    print("-" * 80)

    routing_tests = [
        ("ALLOW", "execute_tools"),
        ("RESTRICT", "respond_restricted"),
        ("ESCALATE", "respond_escalate"),
        ("STOP", "respond_stop"),
    ]

    for action, expected_route in routing_tests:
        state = make_state("test", True, False)
        state["governance_action"] = action
        route = adapter.route_based_on_decision(state)

        passed = route == expected_route
        status = "✓ PASS" if passed else "✗ FAIL"

        print(f"{status}: {action} → {route} (expected: {expected_route})")

        if not passed:
            all_passed = False

    print()
    print("=" * 80)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("=" * 80)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
