# Integration Guide

**Minimal integration: One HTTP call before tool execution**

---

## Core Concept

The governance gate is a **pre-execution check**.

Put it **AFTER** intent recognition, **BEFORE** tool/action execution.

```
User Input
  → Intent Recognition (LLM/classifier)
  → Governance Check (/decision) ← INSERT HERE
  → [if ALLOW] Tool Execution
  → [if not ALLOW] Return decision
```

---

## Three Integration Patterns

### 1. HTTP API (Simplest)

**Best for:** Microservices, multi-language systems, quick prototyping

```python
# Your agent service
import requests

def execute_agent_action(user_input, intent, context, evidence):
    # Step 1: Check governance
    response = requests.post("http://governance-gate:8000/decision", json={
        "intent": {"name": intent, "confidence": 0.95},
        "context": {"user_id": user_id, "channel": "web"},
        "evidence": evidence
    }).json()

    # Step 2: Check decision
    if response["action"] == "ALLOW":
        return execute_tools(intent, context)
    elif response["action"] == "RESTRICT":
        return execute_with_disclaimers(response["rationale"])
    elif response["action"] == "ESCALATE":
        return escalate_to_human(response["rationale"])
    else:  # STOP
        return refuse_request(response["rationale"])

    # Step 3: Log who blocked (for audit)
    print(f"Decision by: {response['final_gate']}")  # "safety", "responsibility", etc.
```

**Deployment:**
```bash
# Run governance gate as separate service
docker run -p 8000:8000 governance-gate:latest

# Or use CLI
govgate serve --host 0.0.0.0 --port 8000
```

---

### 2. Python Library (Lowest Latency)

**Best for:** Same-language systems, high-throughput scenarios

```python
from governance_gate.core.pipeline import GovernancePipeline
from governance_gate.gates import SafetyGate, ResponsibilityGate
from governance_gate.core.types import Intent, Context, Evidence

# Initialize once (startup)
pipeline = GovernancePipeline(gates=[
    SafetyGate(),
    FactVerifiabilityGate(),
    UncertaintyGate(),
    ResponsibilityGate(),
])

def handle_request(user_input, intent, context, evidence):
    # Convert to governance types
    intent_obj = Intent(name=intent, confidence=0.95)
    context_obj = Context(user_id=context["user_id"], channel=context["channel"])
    evidence_obj = Evidence(
        facts=evidence.get("facts", {}),
        rag=evidence.get("rag", {}),
        topic=evidence.get("topic", {})
    )

    # Evaluate
    decision = pipeline.evaluate(intent_obj, context_obj, evidence_obj)

    # Act on decision
    if decision.action == DecisionAction.ALLOW:
        return execute_tools()
    elif decision.action == DecisionAction.ESCALATE:
        return escalate(decision.rationale, decision.final_gate)  # "responsibility"
    # ... handle other actions

    # Audit
    log_decision(
        trace_id=decision.trace_id,
        action=decision.action,
        final_gate=decision.final_gate,  # ← "who blocked?"
        decision_code=decision.decision_code
    )
```

---

### 3. LangGraph Integration (Agent Frameworks)

**Best for:** LangGraph-based agents, complex workflows

```python
from langgraph.graph import StateGraph
from governance_gate.core.types import Intent, Context, Evidence
from governance_gate.core.pipeline import GovernancePipeline
from governance_gate.gates import SafetyGate, ResponsibilityGate

# Initialize pipeline
pipeline = GovernancePipeline(gates=[SafetyGate(), ResponsibilityGate()])

def governance_check(state):
    """Gate before tool execution"""

    # Build intent from LangGraph state
    intent = Intent(
        name=state["intent_name"],
        confidence=state.get("intent_confidence", 0.9),
        parameters={"user_input": state["user_input"]}
    )

    context = Context(
        user_id=state.get("user_id"),
        channel=state.get("channel", "api")
    )

    evidence = Evidence(
        facts=state.get("evidence", {}),
        rag=state.get("rag_context", {}),
        topic=state.get("topic_classification", {})
    )

    # Evaluate
    decision = pipeline.evaluate(intent, context, evidence)

    # Update state with decision
    return {
        "governance_action": decision.action,
        "governance_rationale": decision.rationale,
        "governance_gate": decision.final_gate,  # ← who blocked
        "governance_trace_id": decision.trace_id
    }

# Build graph
workflow = StateGraph(AgentState)

workflow.add_node("intent_recognition", intent_node)
workflow.add_node("governance_check", governance_check)  # ← Gate here
workflow.add_node("tool_execution", tool_node)
workflow.add_node("human_review", human_node)

# Conditional routing based on governance decision
workflow.add_conditional_edges(
    "governance_check",
    lambda state: route_by_governance(state["governance_action"]),
    {
        "allow": "tool_execution",
        "restrict": "respond_with_disclaimers",
        "escalate": "human_review",
        "stop": "refuse_request"
    }
)
```

**Full example:** [examples/langgraph_integration/](../examples/langgraph_integration/)

---

## What Information to Pass

### Minimal (Required)

```json
{
  "intent": {
    "name": "order_status_query",
    "confidence": 0.95
  },
  "context": {
    "user_id": "user_123",
    "channel": "web"
  },
  "evidence": {
    "facts": {},
    "rag": {},
    "topic": {}
  }
}
```

### Complete (Recommended)

```json
{
  "intent": {
    "name": "order_status_query",
    "confidence": 0.95,
    "parameters": {
      "user_input": "Where is my order?",
      "entities": {"order_id": "ORD-123"}
    }
  },
  "context": {
    "user_id": "user_123",
    "channel": "web",
    "session_id": "sess_abc"
  },
  "evidence": {
    "facts": {
      "verifiable": true,
      "verifiable_confidence": 0.9,
      "source": "database"
    },
    "rag": {
      "confidence": 0.85,
      "has_conflicts": false,
      "kb_version": "1.2.3"
    },
    "topic": {
      "has_financial_impact": false,
      "requires_authority": false,
      "is_irreversible": false,
      "is_sensitive": false
    }
  }
}
```

---

## Handling Decision Outcomes

### ALLOW → Proceed normally

```python
if decision["action"] == "ALLOW":
    result = execute_agent_tools(intent, parameters)
    return result
```

### RESTRICT → Respond with constraints

```python
elif decision["action"] == "RESTRICT":
    disclaimer = (
        f"Note: This response is based on general information only. "
        f"Reason: {decision['rationale']}"
    )
    result = execute_agent_tools(intent, parameters)
    return {"response": result, "disclaimer": disclaimer}
```

### ESCALATE → Require human review

```python
elif decision["action"] == "ESCALATE":
    # Create ticket / notify human
    escalation = {
        "intent": intent,
        "rationale": decision["rationale"],
        "gate": decision["final_gate"],  # "responsibility"
        "trace_id": decision["trace_id"],
        "priority": "high" if decision["final_gate"] == "safety" else "medium"
    }

    ticket_id = create_escalation_ticket(escalation)

    return {
        "response": f"Your request requires human review. Ticket: {ticket_id}",
        "escalated": True
    }
```

### STOP → Refuse

```python
elif decision["action"] == "STOP":
    return {
        "response": "I cannot process this request.",
        "reason": decision["rationale"],
        "refused": True
    }
```

---

## Auditing & Monitoring

### Log Decisions

```python
import structlog

log = structlog.get_logger()

log.info(
    "governance_decision",
    trace_id=decision["trace_id"],
    action=decision["action"],
    final_gate=decision["final_gate"],  # ← Aggregate by this
    decision_code=decision["decision_code"],  # ← Aggregate by this too
    intent=intent["name"],
    user_id=context["user_id"]
)
```

### Metrics to Track

```
# Decision rate by action
governance_decisions_total{action="allow"}
governance_decisions_total{action="restrict"}
governance_decisions_total{action="escalate"}
governance_decisions_total{action="stop"}

# Which gates are blocking
governance_final_gate_total{gate="safety"}
governance_final_gate_total{gate="responsibility"}
governance_final_gate_total{gate="fact_verifiability"}
governance_final_gate_total{gate="uncertainty"}

# Top decision codes (trends)
governance_decision_code_total{code="SAFETY_STOP_FRAUD"}
governance_decision_code_total{code="RESPONSIBILITY_ESCALATE_FINANCIAL"}
```

---

## Common Patterns

### Pattern 1: Fraud Detection

```python
# Before payment execution
decision = check_governance(
    intent="payment_bypass",
    evidence={"topic": {"harm_risk": True}}
)

if decision["action"] == "STOP" and decision["final_gate"] == "safety":
    alert_security_team(
        fraud_type="payment_bypass",
        user_id=user_id,
        trace_id=decision["trace_id"]
    )
    block_user(user_id)
```

### Pattern 2: Customer Support Triage

```python
# Before responding to customer
decision = check_governance(
    intent="refund_request",
    evidence={"topic": {"has_financial_impact": True}}
)

if decision["action"] == "ESCALATE" and decision["final_gate"] == "responsibility":
    # Route to human agent instead of bot
    route_to_human_agent(
        intent="refund_request",
        rationale=decision["rationale"],
        priority="high"
    )
```

### Pattern 3: Knowledge Base Updates

```python
# Before answering with RAG
decision = check_governance(
    intent="policy_inquiry",
    evidence={
        "facts": {"verifiable": False, "requires_realtime": True},
        "rag": {"kb_age_days": 45}
    }
)

if decision["action"] == "RESTRICT" and decision["final_gate"] == "fact_verifiability":
    return (
        "I cannot provide current policy information. "
        "Please check the official policy portal or contact support."
    )
```

---

## Troubleshooting

### All decisions are ALLOW

**Problem:** Gate never blocks anything.

**Diagnosis:**
```python
print(decision["gate_decisions"])
# Check if gates are returning None for all inputs
```

**Fix:** Ensure evidence fields match gate expectations.
- `facts.verifiable` for FactVerifiabilityGate
- `rag.confidence` for UncertaintyGate
- `topic.has_financial_impact` for ResponsibilityGate

### Wrong gate is triggering

**Problem:** ResponsibilityGate triggers when SafetyGate should.

**Diagnosis:**
```python
print(decision["final_gate"])  # Check which gate won
print(decision["gate_decisions"])
```

**Fix:** Adjust evidence or gate config. Gates have priority:
1. Safety (STOP first)
2. Fact verifiability (RESTRICT on facts)
3. Uncertainty (RESTRICT on conflicts)
4. Responsibility (ESCALATE on sensitive topics)

### High latency

**Problem:** Governance check adds >100ms latency.

**Solutions:**
- Use Python library (no HTTP overhead)
- Cache pipeline initialization (don't recreate on each request)
- Batch decisions if possible

---

## Observability & Monitoring

### Recommended Log Schema

**Structured JSON log format:**

```json
{
  "timestamp": "2025-02-02T15:13:53Z",
  "level": "info",
  "event": "governance_decision",
  "trace_id": "ff69b873-7b5a-4bc1-a18e-d0814a87cacb",
  "service": "governance-gate",
  "decision": {
    "action": "STOP",
    "final_gate": "safety",
    "decision_code": "SAFETY_STOP_FRAUD",
    "rationale": "Fraud request detected: 'payment system' - ..."
  },
  "context": {
    "intent": "payment_bypass_inquiry",
    "user_id": "user_999",
    "channel": "web"
  },
  "telemetry": {
    "latency_ms": 12.34,
    "policy_version": "1.0",
    "policy_name": "customer_support"
  }
}
```

**Key fields for aggregation:**
- `decision.action` → Aggregate by decision type
- `decision.final_gate` → Aggregate by which gate triggered
- `decision.decision_code` → Aggregate by specific decision reason
- `telemetry.latency_ms` → Track performance
- `trace_id` → Correlate logs across systems

### Recommended Metrics

**Decision Rate (Counter):**
```
governance_decisions_total{action="allow"}
governance_decisions_total{action="restrict"}
governance_decisions_total{action="escalate"}
governance_decisions_total{action="stop"}
```

**Final Gate Distribution (Counter):**
```
governance_final_gate_total{gate="safety"}
governance_final_gate_total{gate="responsibility"}
governance_final_gate_total{gate="fact_verifiability"}
governance_final_gate_total{gate="uncertainty"}
```

**Decision Code Frequency (Counter):**
```
governance_decision_code_total{code="SAFETY_STOP_FRAUD"}
governance_decision_code_total{code="RESPONSIBILITY_ESCALATE_FINANCIAL"}
governance_decision_code_total{code="FACTS_RESTRICT_UNVERIFIABLE"}
```

**Latency (Histogram):**
```
governance_decision_latency_ms_bucket{le="1"}
governance_decision_latency_ms_bucket{le="5"}
governance_decision_latency_ms_bucket{le="10"}
governance_decision_latency_ms_bucket{le="50"}
governance_decision_latency_ms_bucket{le="100"}
governance_decision_latency_ms_bucket{le="+Inf"}
governance_decision_latency_ms_sum
governance_decision_latency_ms_count
```

**Allow Rate (Gauge - % of ALLOW decisions):**
```
governance_allow_rate = (
  governance_decisions_total{action="allow"}
  / governance_decisions_total
) * 100
```

### Example: Python Logging with structlog

```python
import structlog

log = structlog.get_logger()

def log_decision(decision: dict, intent: dict, context: dict):
    """Log governance decision in structured format."""

    log.info(
        "governance_decision",
        trace_id=decision["trace_id"],
        decision={
            "action": decision["action"],
            "final_gate": decision.get("final_gate"),
            "decision_code": decision.get("decision_code"),
            "rationale": decision["rationale"],
        },
        context={
            "intent": intent.get("name"),
            "user_id": context.get("user_id"),
            "channel": context.get("channel"),
        },
        telemetry={
            "latency_ms": decision.get("latency_ms"),
            "policy_version": decision.get("policy_version"),
            "policy_name": decision.get("policy_name"),
        }
    )
```

### Example: Prometheus Metrics Export

```python
from prometheus_client import Counter, Histogram

decision_counter = Counter(
    'governance_decisions_total',
    'Total governance decisions',
    ['action', 'final_gate']
)

decision_latency = Histogram(
    'governance_decision_latency_ms',
    'Decision evaluation latency',
    buckets=[1, 5, 10, 25, 50, 100, 250, 500, 1000]
)

def record_metrics(decision: dict):
    """Record Prometheus metrics."""

    decision_counter.labels(
        action=decision["action"],
        final_gate=decision.get("final_gate", "none")
    ).inc()

    if decision.get("latency_ms"):
        decision_latency.observe(decision["latency_ms"])
```

### Alerting Recommendations

**High STOP Rate (>5%):**
```yaml
alert: HighStopRate
expr: rate(governance_decisions_total{action="stop"}[5m]) / rate(governance_decisions_total[5m]) > 0.05
annotations:
  summary: "Governance gate STOP rate above 5%"
  description: "{{ $value | humanizePercentage }} of requests are blocked"
```

**High Latency (>100ms p95):**
```yaml
alert: HighDecisionLatency
expr: histogram_quantile(0.95, governance_decision_latency_ms) > 100
annotations:
  summary: "Governance decision latency p95 above 100ms"
```

**Safety Gate Spiking (>3x baseline):**
```yaml
alert: SafetyGateSpike
expr: rate(governance_final_gate_total{gate="safety"}[5m]) > 3 * rate(governance_final_gate_total{gate="safety"}[1h] offset 1h)
annotations:
  summary: "Safety gate blocking rate spiked 3x"
  description: "Possible fraud attack or system abuse"
```

---

## Next Steps

1. **Try a case:** `govgate eval examples/case_law/cases/011_fraud_detection/input.json`
2. **Read architecture:** [docs/overview.md](overview.md)
3. **Customize policy:** Edit `policies/presets/customer_support.yaml`
4. **Add your gates:** Extend `gates/` package
5. **Deploy API:** `govgate serve --port 8000`

**Questions?** Open an issue or check existing discussions.
