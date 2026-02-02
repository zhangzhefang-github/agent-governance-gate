"""
Tests for LangGraph integration with Governance Gate.

Tests verify:
1. STOP decisions prevent tool execution
2. ESCALATE decisions prevent tool execution
3. ALLOW decisions proceed to tool execution
4. RESTRICT decisions prevent tool execution
5. Decisions are deterministic (same input = same output)
"""

import sys
import os
from typing import Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../src"))
# Add parent dir to path for adapter import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

# Skip tests if langgraph is not installed
pytest.importorskip("langgraph")

from langgraph.graph import StateGraph, END

from governance_gate.core.types import DecisionAction
from governance_gate.core.pipeline import GovernancePipeline
from governance_gate.gates import FactVerifiabilityGate, UncertaintyGate, ResponsibilityGate
from adapter import AgentState, LangGraphGovernanceAdapter


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def governance_adapter():
    """Create a governance adapter for testing."""
    return LangGraphGovernanceAdapter()


@pytest.fixture
def simple_agent_graph(governance_adapter):
    """
    Build a simple agent graph for testing.

    Graph structure:
    - governance_gate → routing → execute_tools or response
    """
    workflow = StateGraph(AgentState)

    # Mock nodes
    def governance_node(state: AgentState) -> dict[str, Any]:
        return governance_adapter.evaluate_governance(state)

    def execute_tools(state: AgentState) -> dict[str, Any]:
        return {"tool_result": "TOOLS_EXECUTED", "response": "Tool executed successfully"}

    def respond_restricted(state: AgentState) -> dict[str, Any]:
        return {"response": f"RESTRICTED: {state.get('governance_rationale', '')}"}

    def respond_escalate(state: AgentState) -> dict[str, Any]:
        return {"response": f"ESCALATED: {state.get('governance_rationale', '')}"}

    def respond_stop(state: AgentState) -> dict[str, Any]:
        return {"response": f"STOPPED: {state.get('governance_rationale', '')}"}

    # Add nodes
    workflow.add_node("governance_gate", governance_node)
    workflow.add_node("execute_tools", execute_tools)
    workflow.add_node("respond_restricted", respond_restricted)
    workflow.add_node("respond_escalate", respond_escalate)
    workflow.add_node("respond_stop", respond_stop)

    # Set entry point
    workflow.set_entry_point("governance_gate")

    # Conditional routing
    workflow.add_conditional_edges(
        "governance_gate",
        governance_adapter.route_based_on_decision,
        {
            "execute_tools": "execute_tools",
            "respond_restricted": "respond_restricted",
            "respond_escalate": "respond_escalate",
            "respond_stop": "respond_stop",
        },
    )

    # All response nodes lead to END
    workflow.add_edge("execute_tools", END)
    workflow.add_edge("respond_restricted", END)
    workflow.add_edge("respond_escalate", END)
    workflow.add_edge("respond_stop", END)

    return workflow.compile()


# ============================================================================
# Helper Functions
# ============================================================================

def make_test_state(
    intent_name: str = "test_intent",
    confidence: float = 0.9,
    verifiable: bool = True,
    has_financial_impact: bool = False,
    rag_confidence: float = 0.85,
    user_id: str = "test_user",
    channel: str = "test",
) -> AgentState:
    """Create a test state with specified parameters."""
    evidence = {
        "facts": {
            "verifiable": verifiable,
            "verifiable_confidence": 0.9 if verifiable else 0.4,
            "source": "database" if verifiable else "unknown",
            "freshness": "fresh" if verifiable else "stale",
            "requires_realtime": not verifiable,
        },
        "rag": {
            "confidence": rag_confidence,
            "has_conflicts": False,
        },
        "topic": {
            "has_financial_impact": has_financial_impact,
            "requires_authority": False,
            "is_irreversible": False,
            "is_sensitive": False,
        },
    }

    return {
        "user_input": "Test input",
        "intent_name": intent_name,
        "intent_confidence": confidence,
        "intent_parameters": {},
        "user_id": user_id,
        "channel": channel,
        "session_id": "test_session",
        "evidence": evidence,
        "governance_action": None,
        "governance_rationale": None,
        "governance_trace_id": None,
        "tool_result": None,
        "response": None,
    }


# ============================================================================
# Tests: STOP Interrupts Execution
# ============================================================================

class TestStopInterrupts:
    """Tests that STOP decisions prevent tool execution."""

    def test_stop_on_unverifiable_realtime_facts(self, simple_agent_graph):
        """
        Test that STOP prevents tool execution when facts are unverifiable.

        Given:
        - Intent requires real-time facts
        - Facts are not verifiable

        Expected:
        - Decision is STOP or RESTRICT
        - Tools are NOT executed
        - Response does not contain "TOOLS_EXECUTED"
        """
        # Create state with unverifiable facts
        state = make_test_state(
            intent_name="order_status_query",
            verifiable=False,  # Unverifiable facts
        )

        # Run graph
        result = simple_agent_graph.invoke(state)

        # Verify STOP decision
        action = result.get("governance_action")
        assert action in ["STOP", "RESTRICT"], f"Expected STOP or RESTRICT, got {action}"

        # Verify tools were NOT executed
        assert result.get("tool_result") != "TOOLS_EXECUTED", "Tools should not be executed for STOP"

        # Verify response doesn't indicate tool execution
        response = result.get("response", "")
        assert "Tool executed" not in response

    def test_stop_on_conflicting_retrieval(self, governance_adapter):
        """
        Test that STOP on conflicting retrieval prevents execution.

        Given:
        - RAG has conflicting results

        Expected:
        - Decision is STOP (if configured to stop on conflict)
        - Pipeline respects STOP precedence
        """
        # Create adapter that stops on conflicts
        pipeline = GovernancePipeline(
            gates=[
                UncertaintyGate(stop_on_conflict=True),
            ]
        )
        adapter = LangGraphGovernanceAdapter(pipeline=pipeline)

        # Build graph with this adapter
        workflow = StateGraph(AgentState)
        workflow.add_node("governance_gate", lambda s: adapter.evaluate_governance(s))
        workflow.add_node("execute_tools", lambda s: {"tool_result": "TOOLS_EXECUTED"})
        workflow.add_node("respond_stop", lambda s: {"response": "STOPPED"})

        workflow.set_entry_point("governance_gate")
        workflow.add_conditional_edges(
            "governance_gate",
            adapter.route_based_on_decision,
            {
                "execute_tools": "execute_tools",
                "respond_stop": "respond_stop",
            },
        )
        workflow.add_edge("execute_tools", END)
        workflow.add_edge("respond_stop", END)

        graph = workflow.compile()

        # Create state with conflicts
        state = make_test_state()
        state["evidence"]["rag"]["has_conflicts"] = True
        state["evidence"]["rag"]["conflict_count"] = 3

        # Run graph
        result = graph.invoke(state)

        # Verify STOP
        assert result.get("governance_action") == "STOP"
        assert result.get("tool_result") != "TOOLS_EXECUTED"


# ============================================================================
# Tests: ESCALATE Interrupts Execution
# ============================================================================

class TestEscalateInterrupts:
    """Tests that ESCALATE decisions prevent tool execution."""

    def test_escalate_on_financial_impact(self, simple_agent_graph):
        """
        Test that ESCALATE prevents tool execution for financial requests.

        Given:
        - Topic has financial impact

        Expected:
        - Decision is ESCALATE
        - Tools are NOT executed
        - Response indicates escalation
        """
        # Create state with financial impact
        state = make_test_state(
            has_financial_impact=True,  # Financial impact
        )

        # Run graph
        result = simple_agent_graph.invoke(state)

        # Verify ESCALATE decision
        action = result.get("governance_action")
        assert action == "ESCALATE", f"Expected ESCALATE, got {action}"

        # Verify tools were NOT executed
        assert result.get("tool_result") != "TOOLS_EXECUTED", "Tools should not be executed for ESCALATE"

        # Verify response indicates escalation
        response = result.get("response", "")
        assert "ESCALATED" in response.upper()

    def test_escalate_has_trace_id(self, simple_agent_graph):
        """
        Test that ESCALATE decisions include trace ID for audit.

        Given:
        - Topic has financial impact

        Expected:
        - Decision is ESCALATE
        - Trace ID is present
        """
        state = make_test_state(has_financial_impact=True)
        result = simple_agent_graph.invoke(state)

        assert result.get("governance_action") == "ESCALATE"
        assert result.get("governance_trace_id") is not None
        assert len(result.get("governance_trace_id", "")) > 0


# ============================================================================
# Tests: ALLOW Proceeds
# ============================================================================

class TestAllowProceeds:
    """Tests that ALLOW decisions proceed to tool execution."""

    def test_allow_executes_tools(self, simple_agent_graph):
        """
        Test that ALLOW allows tool execution.

        Given:
        - All checks pass

        Expected:
        - Decision is ALLOW
        - Tools ARE executed
        """
        # Create state that should allow
        state = make_test_state(
            verifiable=True,
            has_financial_impact=False,
            rag_confidence=0.9,
        )

        # Run graph
        result = simple_agent_graph.invoke(state)

        # Verify ALLOW decision
        action = result.get("governance_action")
        assert action == "ALLOW", f"Expected ALLOW, got {action}"

        # Verify tools WERE executed
        assert result.get("tool_result") == "TOOLS_EXECUTED", "Tools should be executed for ALLOW"


# ============================================================================
# Tests: RESTRICT Interrupts
# ============================================================================

class TestRestrictInterrupts:
    """Tests that RESTRICT decisions prevent tool execution."""

    def test_restrict_prevents_tool_execution(self, simple_agent_graph):
        """
        Test that RESTRICT prevents tool execution.

        Given:
        - Low RAG confidence

        Expected:
        - Decision is RESTRICT
        - Tools are NOT executed
        """
        # Create state with low confidence
        state = make_test_state(
            verifiable=True,
            rag_confidence=0.4,  # Low confidence
        )

        # Run graph
        result = simple_agent_graph.invoke(state)

        # Verify RESTRICT decision
        action = result.get("governance_action")
        assert action == "RESTRICT", f"Expected RESTRICT, got {action}"

        # Verify tools were NOT executed
        assert result.get("tool_result") != "TOOLS_EXECUTED", "Tools should not be executed for RESTRICT"


# ============================================================================
# Tests: Determinism
# ============================================================================

class TestDeterminism:
    """Tests that decisions are deterministic."""

    def test_same_input_same_output(self, simple_agent_graph):
        """
        Test that identical inputs produce identical decisions.

        Given:
        - Same state executed twice

        Expected:
        - Same action both times
        - Same trace IDs are different (unique per execution)
        - Same rationale
        """
        # Create state
        state = make_test_state(
            intent_name="test_intent",
            verifiable=True,
            has_financial_impact=False,
        )

        # Run graph twice
        result1 = simple_agent_graph.invoke(state)
        result2 = simple_agent_graph.invoke(state)

        # Verify same action
        assert result1.get("governance_action") == result2.get("governance_action")

        # Verify same rationale
        rationale1 = result1.get("governance_rationale")
        rationale2 = result2.get("governance_rationale")
        assert rationale1 == rationale2

        # Trace IDs should be different (unique per execution)
        trace1 = result1.get("governance_trace_id")
        trace2 = result2.get("governance_trace_id")
        assert trace1 != trace2, "Trace IDs should be unique per execution"

    def test_deterministic_ordering(self, governance_adapter):
        """
        Test that decision precedence is deterministic.

        Given:
        - Multiple gates would trigger different actions
        - FactVerifiabilityGate suggests RESTRICT
        - ResponsibilityGate suggests ESCALATE

        Expected:
        - ESCALATE wins (higher precedence)
        """
        # Create pipeline with specific gate order
        pipeline = GovernancePipeline(
            gates=[
                FactVerifiabilityGate(),  # Would RESTRICT
                ResponsibilityGate(),  # Would ESCALATE
            ]
        )
        adapter = LangGraphGovernanceAdapter(pipeline=pipeline)

        # Create state that triggers both gates
        state = make_test_state(
            verifiable=False,  # Triggers RESTRICT from FactVerifiabilityGate
            has_financial_impact=True,  # Triggers ESCALATE from ResponsibilityGate
        )

        # Evaluate
        result = adapter.evaluate_governance(state)

        # ESCALATE should win (higher precedence than RESTRICT)
        assert result["governance_action"] == "ESCALATE"


# ============================================================================
# Tests: State Conversion
# ============================================================================

class TestStateConversion:
    """Tests for state conversion between LangGraph and Governance types."""

    def test_state_to_intent_conversion(self, governance_adapter):
        """Test converting LangGraph state to Intent."""
        state = make_test_state(
            intent_name="test_intent",
            confidence=0.95,
        )

        intent, context, evidence = governance_adapter.state_to_governance_input(state)

        assert intent.name == "test_intent"
        assert intent.confidence == 0.95

    def test_state_to_context_conversion(self, governance_adapter):
        """Test converting LangGraph state to Context."""
        state = make_test_state(
            user_id="test_user",
            channel="test_channel",
        )

        intent, context, evidence = governance_adapter.state_to_governance_input(state)

        assert context.user_id == "test_user"
        assert context.channel == "test_channel"

    def test_state_to_evidence_conversion(self, governance_adapter):
        """Test converting LangGraph state to Evidence."""
        state = make_test_state(
            verifiable=True,
            has_financial_impact=True,
        )

        intent, context, evidence = governance_adapter.state_to_governance_input(state)

        assert evidence.facts["verifiable"] is True
        assert evidence.topic["has_financial_impact"] is True


# ============================================================================
# Tests: Routing
# ============================================================================

class TestRouting:
    """Tests for conditional routing based on decisions."""

    def test_route_allow_to_execute_tools(self, governance_adapter):
        """Test that ALLOW routes to execute_tools."""
        state: AgentState = make_test_state()
        state["governance_action"] = "ALLOW"

        route = governance_adapter.route_based_on_decision(state)
        assert route == "execute_tools"

    def test_route_restrict_to_respond_restricted(self, governance_adapter):
        """Test that RESTRICT routes to respond_restricted."""
        state: AgentState = make_test_state()
        state["governance_action"] = "RESTRICT"

        route = governance_adapter.route_based_on_decision(state)
        assert route == "respond_restricted"

    def test_route_escalate_to_respond_escalate(self, governance_adapter):
        """Test that ESCALATE routes to respond_escalate."""
        state: AgentState = make_test_state()
        state["governance_action"] = "ESCALATE"

        route = governance_adapter.route_based_on_decision(state)
        assert route == "respond_escalate"

    def test_route_stop_to_respond_stop(self, governance_adapter):
        """Test that STOP routes to respond_stop."""
        state: AgentState = make_test_state()
        state["governance_action"] = "STOP"

        route = governance_adapter.route_based_on_decision(state)
        assert route == "respond_stop"

    def test_route_unknown_to_stop(self, governance_adapter):
        """Test that unknown action routes to respond_stop (safe default)."""
        state: AgentState = make_test_state()
        state["governance_action"] = "UNKNOWN_ACTION"

        route = governance_adapter.route_based_on_decision(state)
        assert route == "respond_stop"
