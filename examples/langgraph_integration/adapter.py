"""
Adapter for integrating Governance Gate with LangGraph.

Converts LangGraph state to/from Governance Gate types.
"""

from typing import Any, TypedDict
from dataclasses import asdict

from governance_gate.core.types import Intent, Context, Evidence, DecisionAction
from governance_gate.core.pipeline import GovernancePipeline
from governance_gate.gates import FactVerifiabilityGate, UncertaintyGate, ResponsibilityGate
from governance_gate.policy.loader import PolicyLoader
from governance_gate.policy.evaluator import PolicyEvaluator


class AgentState(TypedDict):
    """
    LangGraph agent state.

    This is the state that flows through the LangGraph nodes.
    """

    # User input
    user_input: str

    # Intent recognition output
    intent_name: str
    intent_confidence: float
    intent_parameters: dict[str, Any]

    # Context information
    user_id: str | None
    channel: str | None
    session_id: str | None

    # Evidence from retrieval/tools
    evidence: dict[str, Any]

    # Governance decision
    governance_action: str | None
    governance_rationale: str | None
    governance_trace_id: str | None

    # Tool execution results
    tool_result: str | None

    # Final response
    response: str | None


class LangGraphGovernanceAdapter:
    """
    Adapter for integrating Governance Gate with LangGraph.

    This adapter:
    1. Converts LangGraph state to Governance types
    2. Evaluates the governance decision
    3. Returns updated state with decision
    """

    def __init__(
        self,
        pipeline: GovernancePipeline | None = None,
        policy_path: str | None = None,
    ) -> None:
        """
        Initialize the adapter.

        Args:
            pipeline: Optional pre-configured governance pipeline
            policy_path: Optional path to policy YAML file
        """
        if pipeline is None:
            # Create default pipeline with all gates
            pipeline = GovernancePipeline(
                gates=[
                    FactVerifiabilityGate(),
                    UncertaintyGate(),
                    ResponsibilityGate(),
                ]
            )

        self.pipeline = pipeline

        # Load policy if provided
        self.policy: PolicyEvaluator | None = None
        if policy_path:
            loader = PolicyLoader(policy_path)
            policy_dict = loader.load()
            self.policy = PolicyEvaluator(policy_dict)

    def state_to_governance_input(self, state: AgentState) -> tuple[Intent, Context, Evidence]:
        """
        Convert LangGraph state to Governance input types.

        Args:
            state: LangGraph agent state

        Returns:
            Tuple of (Intent, Context, Evidence)
        """
        # Build Intent
        intent = Intent(
            name=state.get("intent_name", "unknown"),
            confidence=state.get("intent_confidence", 1.0),
            parameters=state.get("intent_parameters", {}),
        )

        # Build Context
        context = Context(
            user_id=state.get("user_id"),
            channel=state.get("channel"),
            session_id=state.get("session_id"),
        )

        # Extract evidence from state
        evidence_dict = state.get("evidence", {})

        # Build Evidence with defaults
        evidence = Evidence(
            facts=evidence_dict.get("facts", {}),
            rag=evidence_dict.get("rag", {}),
            topic=evidence_dict.get("topic", {}),
            metadata=evidence_dict.get("metadata", {}),
        )

        return intent, context, evidence

    def decision_to_state_update(
        self, state: AgentState, decision
    ) -> dict[str, Any]:
        """
        Convert governance decision to LangGraph state update.

        Args:
            state: Current LangGraph state
            decision: Governance decision object

        Returns:
            Dictionary of state updates
        """
        return {
            "governance_action": decision.action.value,
            "governance_rationale": decision.rationale,
            "governance_trace_id": decision.trace_id,
        }

    def evaluate_governance(self, state: AgentState) -> dict[str, Any]:
        """
        Evaluate governance gate and return state updates.

        This is the main method called from the LangGraph governance node.

        Args:
            state: Current LangGraph state

        Returns:
            State updates with governance decision
        """
        # Convert state to governance input
        intent, context, evidence = self.state_to_governance_input(state)

        # Evaluate governance
        decision = self.pipeline.evaluate(intent, context, evidence, self.policy)

        # Convert decision back to state update
        return self.decision_to_state_update(state, decision)

    @staticmethod
    def route_based_on_decision(state: AgentState) -> str:
        """
        Route to next node based on governance decision.

        Args:
            state: Current LangGraph state

        Returns:
            Name of next node to route to
        """
        action = state.get("governance_action", "ALLOW")

        if action == "ALLOW":
            return "execute_tools"
        elif action == "RESTRICT":
            return "respond_restricted"
        elif action == "ESCALATE":
            return "respond_escalate"
        elif action == "STOP":
            return "respond_stop"
        else:
            return "respond_stop"


def create_default_adapter(policy_path: str | None = None) -> LangGraphGovernanceAdapter:
    """
    Create a default governance adapter.

    Args:
        policy_path: Optional path to policy YAML file

    Returns:
        Configured LangGraphGovernanceAdapter
    """
    return LangGraphGovernanceAdapter(policy_path=policy_path)


def create_customer_support_adapter() -> LangGraphGovernanceAdapter:
    """
    Create a governance adapter with customer support policy.

    Returns:
        Configured LangGraphGovernanceAdapter with customer support policy
    """
    policy_path = "../../policies/presets/customer_support.yaml"
    return LangGraphGovernanceAdapter(policy_path=policy_path)
