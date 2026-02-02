"""
Customer Support Integration Example

Shows how to integrate governance gate into a customer support agent workflow.
"""

import requests
import os
from typing import Dict, Any, Optional

# Configuration
GATE_API_URL = os.environ.get(
    "GATE_API_URL",
    "http://localhost:8000/decision"
)
POLICY_PATH = os.environ.get(
    "GATE_POLICY_PATH",
    "starter-kits/customer_support/policy.yaml"
)


class CustomerSupportAgent:
    """
    Customer support agent with governance gate integration.

    The gate is consulted BEFORE taking any action.
    """

    def __init__(self):
        self.session = requests.Session()

    def handle_request(
        self,
        user_input: str,
        intent: str,
        intent_confidence: float,
        user_id: str,
        channel: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle a customer support request with governance check.

        Args:
            user_input: Raw customer message
            intent: Recognized intent (e.g., "refund_request", "order_status_query")
            intent_confidence: Intent recognition confidence (0-1)
            user_id: Customer identifier
            channel: Communication channel (web/email/chat/phone)
            additional_context: Optional additional context

        Returns:
            Response dict with action and result
        """

        # Step 1: Prepare evidence for governance gate
        evidence = self._collect_evidence(user_input, intent, additional_context)

        # Step 2: Check governance gate
        decision = self._check_governance(
            intent=intent,
            intent_confidence=intent_confidence,
            user_id=user_id,
            channel=channel,
            evidence=evidence
        )

        # Step 3: Act based on governance decision
        return self._execute_decision(decision, user_input, intent, additional_context)

    def _collect_evidence(
        self,
        user_input: str,
        intent: str,
        additional_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Collect evidence for governance evaluation."""

        evidence = {
            "facts": {
                "verifiable": True,  # TODO: Check based on data availability
                "verifiable_confidence": 0.9,  # TODO: From actual data sources
                "source": "database",
                "requires_realtime": intent in ["order_status_query", "refund_status_query"]
            },
            "rag": {
                "confidence": 0.85,  # TODO: From RAG system
                "has_conflicts": False,
                "kb_age_days": 5  # TODO: From knowledge base metadata
            },
            "topic": {
                "has_financial_impact": intent in [
                    "refund_request", "compensation_request",
                    "credit_request", "discount_request"
                ],
                "requires_authority": intent in [
                    "policy_change", "exception_request", "account_closure"
                ],
                "is_irreversible": intent == "account_closure",
                "is_sensitive": intent in ["legal_threat", "regulatory_complaint"],
                "harm_risk": False
            }
        }

        # Override with additional context if provided
        if additional_context:
            evidence.update(additional_context.get("evidence", {}))

        return evidence

    def _check_governance(
        self,
        intent: str,
        intent_confidence: float,
        user_id: str,
        channel: str,
        evidence: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Consult governance gate for decision.

        Returns:
            Decision dict with action, final_gate, rationale, etc.
        """

        try:
            response = self.session.post(
                GATE_API_URL,
                json={
                    "intent": {
                        "name": intent,
                        "confidence": intent_confidence,
                        "parameters": {"user_input": evidence.get("user_input", "")}
                    },
                    "context": {
                        "user_id": user_id,
                        "channel": channel
                    },
                    "evidence": evidence,
                    "policy_path": POLICY_PATH
                },
                timeout=2.0  # 2 second timeout
            )

            response.raise_for_status()
            decision = response.json()

            # Log decision for observability
            self._log_decision(decision, intent, user_id)

            return decision

        except requests.exceptions.RequestException as e:
            # Fallback: ESCALATE on error (fail-closed)
            return {
                "action": "ESCALATE",
                "final_gate": None,
                "rationale": f"Governance gate unavailable: {str(e)}",
                "trace_id": None,
                "error": "governance_unavailable"
            }

    def _execute_decision(
        self,
        decision: Dict[str, Any],
        user_input: str,
        intent: str,
        additional_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute the appropriate action based on governance decision."""

        action = decision["action"]

        if action == "ALLOW":
            # Proceed with normal agent handling
            result = self._handle_normally(user_input, intent, additional_context)
            return {
                "status": "completed",
                "governance_action": "ALLOW",
                "result": result,
                "trace_id": decision["trace_id"]
            }

        elif action == "RESTRICT":
            # Handle with constraints/disclaimers
            result = self._handle_with_restrictions(
                user_input, intent, decision["rationale"]
            )
            return {
                "status": "restricted",
                "governance_action": "RESTRICT",
                "result": result,
                "rationale": decision["rationale"],
                "trace_id": decision["trace_id"],
                "final_gate": decision["final_gate"]
            }

        elif action == "ESCALATE":
            # Escalate to human
            ticket_id = self._escalate_to_human(
                user_input, intent, decision["rationale"], decision["final_gate"]
            )
            return {
                "status": "escalated",
                "governance_action": "ESCALATE",
                "ticket_id": ticket_id,
                "rationale": decision["rationale"],
                "trace_id": decision["trace_id"],
                "final_gate": decision["final_gate"]
            }

        elif action == "STOP":
            # Refuse to process
            return {
                "status": "refused",
                "governance_action": "STOP",
                "message": "I cannot process this request.",
                "rationale": decision["rationale"],
                "trace_id": decision["trace_id"],
                "final_gate": decision["final_gate"]
            }

        else:
            # Unknown action - escalate for safety
            return {
                "status": "escalated",
                "governance_action": "UNKNOWN",
                "reason": f"Unknown governance action: {action}"
            }

    def _handle_normally(
        self,
        user_input: str,
        intent: str,
        additional_context: Optional[Dict[str, Any]]
    ) -> str:
        """Normal agent handling (when governance allows)."""

        # TODO: Implement actual agent logic
        return f"Processed {intent}: {user_input[:50]}..."

    def _handle_with_restrictions(
        self,
        user_input: str,
        intent: str,
        rationale: str
    ) -> str:
        """Handle with disclaimers due to governance restriction."""

        disclaimer = (
            f"Note: This response is based on general information only. "
            f"Reason: {rationale}"
        )

        # TODO: Implement actual response logic
        return f"{disclaimer}\n\nLimited response for {intent}"

    def _escalate_to_human(
        self,
        user_input: str,
        intent: str,
        rationale: str,
        final_gate: Optional[str]
    ) -> str:
        """Escalate to human agent."""

        # TODO: Create ticket in your ticketing system
        ticket_id = f"TICKET-{intent.upper()}-{hash(user_input) % 10000:04d}"

        # TODO: Notify human agents
        # For example: Slack notification, email, etc.

        return ticket_id

    def _log_decision(
        self,
        decision: Dict[str, Any],
        intent: str,
        user_id: str
    ):
        """Log governance decision for observability."""

        # TODO: Replace with your logging system
        # Example: structlog, loguru, or standard logging

        log_entry = {
            "event": "governance_decision",
            "trace_id": decision["trace_id"],
            "intent": intent,
            "user_id": user_id,
            "decision": {
                "action": decision["action"],
                "final_gate": decision.get("final_gate"),
                "decision_code": decision.get("decision_code"),
                "rationale": decision["rationale"]
            },
            "telemetry": {
                "latency_ms": decision.get("latency_ms"),
                "policy_version": decision.get("policy_version"),
                "policy_name": decision.get("policy_name")
            }
        }

        # Example: structured JSON logging
        import json
        print(json.dumps(log_entry))

        # TODO: Send to your observability platform
        # - ELK / Splunk
        # - Prometheus
        # - DataDog / New Relic


# Example usage
if __name__ == "__main__":
    agent = CustomerSupportAgent()

    # Example 1: Simple query (should ALLOW)
    result = agent.handle_request(
        user_input="Where is my order #12345?",
        intent="order_status_query",
        intent_confidence=0.95,
        user_id="customer_001",
        channel="web"
    )
    print(f"Result: {result['governance_action']} - {result.get('status')}")

    # Example 2: Refund request (should ESCALATE)
    result = agent.handle_request(
        user_input="I want a refund for my order",
        intent="refund_request",
        intent_confidence=0.92,
        user_id="customer_002",
        channel="email"
    )
    print(f"Result: {result['governance_action']} - ticket: {result.get('ticket_id')}")
