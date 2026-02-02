"""
Runnable LangGraph agent with Governance Gate integration.

This example demonstrates:
1. A simple LangGraph agent with intent recognition and tool execution
2. Governance gate inserted between intent and execution
3. Deterministic routing based on governance decision
4. No LLM calls - all logic is rule-based
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))

from typing import Literal
from typing_extensions import TypedDict

try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
except ImportError:
    print("Error: langgraph is not installed.")
    print("Install with: pip install langgraph langchain-core")
    sys.exit(1)

from governance_gate.core.types import DecisionAction
from adapter import (
    AgentState,
    LangGraphGovernanceAdapter,
    create_customer_support_adapter,
)


# ============================================================================
# Mock Functions (no LLM calls)
# ============================================================================

def mock_intent_recognition(state: AgentState) -> dict[str, Any]:
    """
    Mock intent recognition (normally would use LLM).

    Uses simple keyword matching to simulate intent recognition.
    """
    user_input = state["user_input"].lower()

    # Simple keyword-based intent classification
    if "how do i" in user_input or "how to" in user_input:
        intent_name = "order_status_query"
        confidence = 0.95
        parameters = {"user_input": state["user_input"]}
        requires_realtime = False
        has_financial_impact = False
    elif "why not" in user_input or "not shipped" in user_input:
        intent_name = "order_status_query"
        confidence = 0.92
        parameters = {"user_input": state["user_input"]}
        requires_realtime = True
        has_financial_impact = False
    elif "compensat" in user_input or "refund" in user_input:
        intent_name = "order_status_query"
        confidence = 0.90
        parameters = {"user_input": state["user_input"]}
        requires_realtime = False
        has_financial_impact = True
    else:
        intent_name = "general_query"
        confidence = 0.85
        parameters = {"user_input": state["user_input"]}
        requires_realtime = False
        has_financial_impact = False

    # Build mock evidence
    evidence = {
        "facts": {
            "verifiable": not requires_realtime,  # Unverifiable if requires realtime
            "verifiable_confidence": 0.9 if not requires_realtime else 0.4,
            "source": "database" if not requires_realtime else "unknown",
            "freshness": "fresh" if not requires_realtime else "stale",
            "requires_realtime": requires_realtime,
        },
        "rag": {
            "confidence": confidence,
            "source": "vector_db",
            "has_conflicts": False,
            "kb_age_days": 5,
        },
        "topic": {
            "has_financial_impact": has_financial_impact,
            "requires_authority": False,
            "is_irreversible": False,
            "is_sensitive": False,
        },
    }

    return {
        "intent_name": intent_name,
        "intent_confidence": confidence,
        "intent_parameters": parameters,
        "evidence": evidence,
    }


def mock_tool_execution(state: AgentState) -> dict[str, Any]:
    """
    Mock tool execution (normally would call actual tools/APIs).

    Only executes if governance allowed it.
    """
    intent = state["intent_name"]
    params = state["intent_parameters"]

    # Simulate different tool responses based on intent
    if intent == "order_status_query":
        result = (
            "To check your order status:\n"
            "1. Go to myaccount.com/orders\n"
            "2. Enter your order number\n"
            "3. View real-time status"
        )
    else:
        result = f"Executed tools for intent: {intent}"

    return {"tool_result": result}


# ============================================================================
# Governance Node
# ============================================================================

def governance_gate_node(state: AgentState, adapter) -> dict[str, Any]:
    """
    Governance gate node - evaluates if request should proceed.

    This node:
    1. Converts LangGraph state to governance input
    2. Evaluates governance decision
    3. Returns decision in state

    The routing function will use this decision to determine next step.
    """
    return adapter.evaluate_governance(state)


# ============================================================================
# Response Nodes
# ============================================================================

def respond_allowed(state: AgentState) -> dict[str, Any]:
    """Generate response for ALLOW decision - proceed with tool execution."""
    return {"response": "Governance: ALLOWED - Proceeding with execution"}


def respond_restricted(state: AgentState) -> dict[str, Any]:
    """Generate response for RESTRICT decision - constrained response."""
    rationale = state.get("governance_rationale", "Governance restriction applied")
    return {
        "response": f"Governance: RESTRICTED\n\n{rationale}\n\nI can provide general guidance, but cannot complete this specific request due to the above restrictions."
    }


def respond_escalate(state: AgentState) -> dict[str, Any]:
    """Generate response for ESCALATE decision - requires human review."""
    rationale = state.get("governance_rationale", "Requires human review")
    trace_id = state.get("governance_trace_id", "unknown")
    return {
        "response": f"Governance: ESCALATED\n\n{rationale}\n\nYour request has been escalated to a human agent for review.\n\nTrace ID: {trace_id}"
    }


def respond_stop(state: AgentState) -> dict[str, Any]:
    """Generate response for STOP decision - cannot proceed."""
    rationale = state.get("governance_rationale", "Cannot proceed")
    return {
        "response": f"Governance: STOP\n\n{rationale}\n\nI cannot assist with this request. Please contact support for assistance."
    }


def execute_tools_node(state: AgentState) -> dict[str, Any]:
    """Execute tools and generate final response."""
    # Execute tools
    tool_result = mock_tool_execution(state)

    # Format response
    response = f"{tool_result}"

    return {"response": response}


# ============================================================================
# Graph Building
# ============================================================================

def build_agent_graph(adapter: LangGraphGovernanceAdapter):
    """
    Build the LangGraph agent with governance gate.

    Flow:
    1. intent_recognition - Recognize user intent
    2. governance_gate - Evaluate governance decision
    3. [routing] - Route based on decision
       - ALLOW → execute_tools → respond_allowed → END
       - RESTRICT → respond_restricted → END
       - ESCALATE → respond_escalate → END
       - STOP → respond_stop → END
    """
    # Create the graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("intent_recognition", mock_intent_recognition)
    workflow.add_node("governance_gate", lambda s: governance_gate_node(s, adapter))
    workflow.add_node("execute_tools", execute_tools_node)
    workflow.add_node("respond_allowed", respond_allowed)
    workflow.add_node("respond_restricted", respond_restricted)
    workflow.add_node("respond_escalate", respond_escalate)
    workflow.add_node("respond_stop", respond_stop)

    # Set entry point
    workflow.set_entry_point("intent_recognition")

    # Add edges
    workflow.add_edge("intent_recognition", "governance_gate")

    # Conditional routing from governance_gate
    workflow.add_conditional_edges(
        "governance_gate",
        adapter.route_based_on_decision,
        {
            "execute_tools": "execute_tools",
            "respond_restricted": "respond_restricted",
            "respond_escalate": "respond_escalate",
            "respond_stop": "respond_stop",
        },
    )

    # Execute tools → respond_allowed → END
    workflow.add_edge("execute_tools", "respond_allowed")

    # All response nodes lead to END
    workflow.add_edge("respond_allowed", END)
    workflow.add_edge("respond_restricted", END)
    workflow.add_edge("respond_escalate", END)
    workflow.add_edge("respond_stop", END)

    # Compile the graph
    return workflow.compile()


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Run the LangGraph agent with governance gate."""
    print("=" * 80)
    print("LangGraph Agent with Governance Gate")
    print("=" * 80)
    print()

    # Create adapter with customer support policy
    adapter = create_customer_support_adapter()

    # Build the graph
    graph = build_agent_graph(adapter)

    # Test cases
    test_cases = [
        {
            "name": "Case 1: ALLOW - How to check order status",
            "input": "How do I check my order status?",
            "expected": "ALLOW",
        },
        {
            "name": "Case 2: RESTRICT - Why order not shipped",
            "input": "Why has my order not shipped yet?",
            "expected": "RESTRICT",
        },
        {
            "name": "Case 3: ESCALATE - Compensation request",
            "input": "You messed up my order, you should compensate me",
            "expected": "ESCALATE",
        },
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"{test['name']}")
        print(f"{'=' * 80}")
        print(f"User Input: {test['input']}")
        print(f"Expected: {test['expected']}")
        print()

        # Create initial state
        initial_state: AgentState = {
            "user_input": test["input"],
            "intent_name": "",
            "intent_confidence": 0.0,
            "intent_parameters": {},
            "user_id": "user_123",
            "channel": "web",
            "session_id": f"session_{i}",
            "evidence": {},
            "governance_action": None,
            "governance_rationale": None,
            "governance_trace_id": None,
            "tool_result": None,
            "response": None,
        }

        # Run the graph
        result = graph.invoke(initial_state)

        # Print results
        print(f"\nActual Action: {result.get('governance_action', 'N/A')}")
        print(f"Trace ID: {result.get('governance_trace_id', 'N/A')}")
        print()
        print("-" * 80)
        print("RESPONSE:")
        print("-" * 80)
        print(result.get("response", "No response"))
        print()

        # Verify result matches expected
        actual = result.get("governance_action")
        expected = test["expected"]
        status = "✓ PASS" if actual == expected else "✗ FAIL"
        print(f"{status}: Expected {expected}, got {actual}")

    print("\n" + "=" * 80)
    print("Demo complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
