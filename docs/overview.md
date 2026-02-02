# Governance Gate Overview

## Architecture

The Governance Gate is a decision engine that sits **after intent recognition** and **before agent execution**. It evaluates whether a request is safe to proceed autonomously based on three orthogonal dimensions:

1. **Fact Verifiability** - Are the required facts available and trusted?
2. **Uncertainty Exposure** - Is the system's confidence within acceptable bounds?
3. **Responsibility Boundary** - Does the request require human authority?

```
User Input
  → Intent Recognition (LLM/Classifier)
    → Governance Gate (this project)
      → Decision: ALLOW / RESTRICT / ESCALATE / STOP
        → Agent Execution (if ALLOW)
```

## Decision Pipeline

The pipeline consists of three **gates** that are evaluated sequentially:

1. **FactVerifiabilityGate** - Checks if facts can be verified
2. **UncertaintyGate** - Checks if uncertainty is within bounds
3. **ResponsibilityGate** - Checks if responsibility boundaries are respected

Each gate returns one of:
- `None` - Continue with current decision (annotate only)
- `DecisionAction` - Override with new action (if higher precedence)

## Decision Actions

| Action | Description | Example |
|--------|-------------|---------|
| **ALLOW** | Safe to proceed autonomously | User asks for help documentation |
| **RESTRICT** | Respond with constraints/disclaimers only | User asks about real-time order status but facts are unverifiable |
| **ESCALATE** | Require human review | User requests compensation |
| **STOP** | Do not continue | Conflicting retrieval results |

## Precedence Rules

When multiple gates trigger, actions are combined using **precedence**:

```
STOP > ESCALATE > RESTRICT > ALLOW
```

For example:
- If FactVerifiabilityGate suggests RESTRICT and ResponsibilityGate suggests ESCALATE → **ESCALATE** wins
- If UncertaintyGate suggests STOP and ResponsibilityGate suggests ESCALATE → **STOP** wins

## Gate Logic

### FactVerifiabilityGate

Evaluates whether facts required to fulfill the intent are verifiable.

**Rules:**
- If `facts.verifiable == false` AND intent requires real-time facts → **RESTRICT** or **STOP**
- If `facts.verifiable_confidence < threshold` → **RESTRICT** (if real-time) or annotate
- If `facts.source in ["unknown", "untrusted"]` → **RESTRICT** (if real-time) or annotate
- If `facts.freshness in ["stale", "outdated"]` → **RESTRICT**

**Configuration:**
```yaml
gates:
  fact_verifiability:
    require_realtime_facts: ["order_status_query", "account_balance_query"]
    verifiable_threshold: 0.7
    stop_on_unverifiable: false
```

### UncertaintyGate

Evaluates whether uncertainty is within acceptable bounds.

**Rules:**
- If `rag.confidence < threshold` → **RESTRICT**
- If `rag.has_conflicts == true` → **RESTRICT** or **STOP**
- If `rag.kb_age_days > threshold` → **RESTRICT**
- If `rag.tool_disagreement == true` → **ESCALATE**

**Configuration:**
```yaml
gates:
  uncertainty:
    confidence_threshold: 0.6
    stop_on_conflict: false
    outdated_version_days: 30
```

### ResponsibilityGate

Evaluates whether the request crosses responsibility boundaries.

**Rules:**
- If intent in `financial_intents` OR `topic.has_financial_impact == true` → **ESCALATE**
- If intent in `authority_intents` OR `topic.requires_authority == true` → **ESCALATE**
- If `topic.is_irreversible == true` → **ESCALATE**
- If `topic.is_sensitive == true` → **ESCALATE** or **STOP**

**Configuration:**
```yaml
gates:
  responsibility:
    financial_intents: ["refund", "compensation", "discount_approval"]
    authority_intents: ["policy_change", "contract_modification"]
    sensitive_intents: ["legal_advice", "medical_advice"]
    stop_on_sensitive: false
```

## Policy System

Policies are **YAML files** that define:

1. **Gate configurations** - Thresholds and settings for each gate
2. **Rules** - Condition → Action mappings that override or supplement gate logic

Policies are evaluated **before** gates and can short-circuit evaluation.

### Example Policy Rule

```yaml
rules:
  - name: compensate_keyword
    priority: 90
    conditions:
      intent.parameters.user_input:
        contains: "compensat"
    action: ESCALATE
    reason: Compensation request detected - requires human review
```

## Evidence Structure

Evidence is collected about the intent, context, and environment:

```python
Evidence(
    facts={
        "verifiable": True,
        "verifiable_confidence": 0.9,
        "source": "database",
        "freshness": "fresh",
        "requires_realtime": False,
    },
    rag={
        "confidence": 0.85,
        "has_conflicts": False,
        "kb_version": "1.2.3",
        "kb_age_days": 5,
    },
    topic={
        "has_financial_impact": False,
        "requires_authority": False,
        "is_irreversible": False,
        "is_sensitive": False,
    }
)
```

## Decision Output

Every decision includes:

```json
{
  "action": "ALLOW",
  "rationale": "All gates passed - safe to proceed",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "evidence_summary": {
    "intent": "order_status_query",
    "context": {"channel": "web"}
  },
  "gate_contributions": {
    "fact_verifiability": "Facts are verifiable",
    "uncertainty": "Uncertainty is acceptable",
    "responsibility": "Within responsibility boundaries"
  },
  "required_steps": []
}
```

## Case Law: Same Intent, Different Decisions

The power of the governance gate is demonstrated by how the **same intent** can lead to **different decisions** based on context:

### Intent: `order_status_query`

**Case 1 - ALLOW:**
- User: "How do I check my order status?"
- Evidence: Facts verifiable, high confidence, no financial impact
- Decision: **ALLOW** (informational only)

**Case 2 - RESTRICT:**
- User: "Why has my order not shipped yet?"
- Evidence: Requires real-time facts but facts not verifiable
- Decision: **RESTRICT** (unverifiable real-time facts)

**Case 3 - ESCALATE:**
- User: "You messed up my order, you should compensate me"
- Evidence: Financial impact detected
- Decision: **ESCALATE** (financial responsibility)

This demonstrates that **intent is not destiny** - context and evidence determine the outcome.

## Extending the System

### Adding a New Gate

Create a new gate class that inherits from `Gate`:

```python
from governance_gate.core.pipeline import Gate
from governance_gate.core.types import DecisionAction

class MyCustomGate(Gate):
    name = "my_custom_gate"

    def evaluate(self, intent, context, evidence, policy=None):
        # Your logic here
        if some_condition:
            return DecisionAction.RESTRICT, "Reason for restriction"
        return None, "No issues detected"
```

### Adding Policy Rules

Add rules to your policy YAML:

```yaml
rules:
  - name: my_custom_rule
    priority: 50
    conditions:
      intent.name:
        in: ["high_risk_intent_1", "high_risk_intent_2"]
      context.channel:
        equals: "api"
    action: ESCALATE
    reason: High-risk intent via API requires review
```

### Supported Condition Operators

- **Equality**: `equals`, `not_equals`
- **Membership**: `in`, `not_in`, `contains`, `not_contains`
- **Numeric**: `gt`, `gte`, `lt`, `lte`, `between`
- **Boolean**: `is_true`, `is_false`, `is_null`, `is_not_null`
- **Collections**: `any_of`, `all_of`
- **Pattern**: `matches`, `starts_with`, `ends_with`
