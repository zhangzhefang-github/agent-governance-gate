# Policy Language Reference

## Policy File Structure

A policy file is a YAML document that defines governance rules and gate configurations.

```yaml
version: "1.0"
name: my_policy
description: "Policy description"

gates:
  fact_verifiability:
    # Config
  uncertainty:
    # Config
  responsibility:
    # Config

rules:
  - name: rule_name
    priority: 100
    conditions:
      # conditions
    action: ALLOW|RESTRICT|ESCALATE|STOP
    reason: "Human-readable reason"
    enabled: true

metadata:
  # optional metadata
```

## Top-Level Fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `version` | Yes | string | Policy version (must be "1.x") |
| `name` | Yes | string | Unique policy name |
| `description` | No | string | Human-readable description |
| `gates` | No | object | Gate-specific configurations |
| `rules` | Yes | array | List of policy rules |
| `metadata` | No | object | Optional metadata |

## Gate Configuration

Gate configurations override default gate behavior.

### fact_verifiability

```yaml
gates:
  fact_verifiability:
    require_realtime_facts:
      - order_status_query
      - account_balance_query
    verifiable_threshold: 0.7
    stop_on_unverifiable: false
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `require_realtime_facts` | array | `[]` | Intents requiring real-time facts |
| `verifiable_threshold` | float | `0.7` | Min confidence for verifiability |
| `stop_on_unverifiable` | boolean | `false` | STOP vs RESTRICT on unverifiable |

### uncertainty

```yaml
gates:
  uncertainty:
    confidence_threshold: 0.6
    stop_on_conflict: false
    outdated_version_days: 30
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `confidence_threshold` | float | `0.6` | Min RAG confidence |
| `stop_on_conflict` | boolean | `false` | STOP vs RESTRICT on conflicts |
| `outdated_version_days` | int | `30` | Days before KB is outdated |

### responsibility

```yaml
gates:
  responsibility:
    financial_intents:
      - refund
      - compensation
    authority_intents:
      - policy_change
    sensitive_intents:
      - legal_advice
    stop_on_sensitive: false
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `financial_intents` | array | `["refund", ...]` | Intents with financial impact |
| `authority_intents` | array | `["policy_change", ...]` | Intents requiring authority |
| `sensitive_intents` | array | `["legal_advice", ...]` | Sensitive intent names |
| `stop_on_sensitive` | boolean | `false` | STOP vs ESCALATE on sensitive |

## Rules

Rules are evaluated in priority order (higher priority first). The first matching rule determines the action.

### Rule Structure

```yaml
rules:
  - name: rule_name           # Required: unique rule name
    priority: 100             # Optional: higher = evaluated first (default: 0)
    enabled: true             # Optional: whether rule is active (default: true)
    conditions:               # Required: condition dictionary
      field.path:
        operator: value
    action: ESCALATE          # Required: ALLOW|RESTRICT|ESCALATE|STOP
    reason: "Explanation"     # Optional: human-readable reason
```

## Conditions

Conditions use **dotted path notation** to reference fields:

### Field Paths

| Path | Description |
|------|-------------|
| `intent.name` | Intent name |
| `intent.confidence` | Intent confidence (0-1) |
| `intent.parameters.*` | Intent parameters |
| `context.user_id` | User ID |
| `context.channel` | Communication channel |
| `context.session_id` | Session ID |
| `context.metadata.*` | Custom context metadata |
| `evidence.facts.*` | Fact verifiability fields |
| `evidence.rag.*` | RAG/retrieval fields |
| `evidence.topic.*` | Topic sensitivity fields |

### Operators

#### Equality Operators

```yaml
conditions:
  intent.name:
    equals: "order_status_query"
  context.channel:
    not_equals: "api"
```

| Operator | Description | Example Value |
|----------|-------------|---------------|
| `equals` | Exact match | `"order_status_query"` |
| `not_equals` | Not equal | `"api"` |

#### Membership Operators

```yaml
conditions:
  intent.name:
    in: ["intent_1", "intent_2"]
  context.channel:
    not_in: ["api", "webhook"]
  intent.parameters.user_input:
    contains: "refund"
  intent.parameters.user_input:
    not_contains: "test"
```

| Operator | Description | Example Value |
|----------|-------------|---------------|
| `in` | Value in list | `["a", "b"]` |
| `not_in` | Value not in list | `["x", "y"]` |
| `contains` | String contains substring | `"refund"` |
| `not_contains` | String does not contain | `"test"` |

#### Numeric Operators

```yaml
conditions:
  intent.confidence:
    gte: 0.9
  evidence.rag.confidence:
    lt: 0.6
  evidence.rag.kb_age_days:
    between: [0, 30]
```

| Operator | Description | Example Value |
|----------|-------------|---------------|
| `gt` | Greater than | `0.5` |
| `gte` | Greater than or equal | `0.9` |
| `lt` | Less than | `0.6` |
| `lte` | Less than or equal | `1.0` |
| `between` | In range (inclusive) | `[0, 30]` |

#### Boolean Operators

```yaml
conditions:
  evidence.facts.verifiable:
    is_true: true
  evidence.rag.has_conflicts:
    is_false: true
  context.user_id:
    is_null: false
  evidence.facts.source:
    is_not_null: true
```

| Operator | Description | Value |
|----------|-------------|-------|
| `is_true` | Value is true | `true` |
| `is_false` | Value is false | `true` |
| `is_null` | Value is null/None | `true` |
| `is_not_null` | Value is not null | `true` |

#### Collection Operators

```yaml
conditions:
  intent.parameters.tags:
    any_of: ["urgent", "high_priority"]
  intent.parameters.permissions:
    all_of: ["read", "write"]
```

| Operator | Description | Example Value |
|----------|-------------|---------------|
| `any_of` | Any value in list | `["a", "b"]` |
| `all_of` | All values in list | `["x", "y"]` |

#### Pattern Operators

```yaml
conditions:
  intent.order_id:
    matches: "^ORD-\\d+$"
  intent.parameters.user_input:
    starts_with: "refund"
  intent.parameters.user_input:
    ends_with: "please"
```

| Operator | Description | Example Value |
|----------|-------------|---------------|
| `matches` | Regex match | `"^ORD-\\d+$"` |
| `starts_with` | String starts with | `"refund"` |
| `ends_with` | String ends with | `"please"` |

## Compound Conditions

Multiple conditions in a rule use **AND logic** (all must match):

```yaml
rules:
  - name: high_confidence_api
    conditions:
      intent.confidence:
        gte: 0.9
      context.channel:
        equals: "api"
      evidence.rag.confidence:
        gte: 0.7
    action: ALLOW
```

## Complete Policy Example

```yaml
version: "1.0"
name: customer_support_triage
description: "Governance policy for customer support"

gates:
  fact_verifiability:
    require_realtime_facts:
      - order_status_query
    verifiable_threshold: 0.7
  uncertainty:
    confidence_threshold: 0.6
  responsibility:
    financial_intents:
      - refund
      - compensation

rules:
  # High confidence API calls can auto-allow
  - name: high_confidence_api
    priority: 100
    conditions:
      intent.confidence:
        gte: 0.9
      context.channel:
        equals: "api"
      evidence.rag.confidence:
        gte: 0.7
      evidence.topic.has_financial_impact:
        is_false: true
    action: ALLOW
    reason: API channel with high confidence - safe to proceed

  # Low confidence should restrict
  - name: low_intent_confidence
    priority: 90
    conditions:
      intent.confidence:
        lt: 0.7
    action: RESTRICT
    reason: Intent confidence is low - request clarification

  # Compensation keyword escalates
  - name: compensate_keyword
    priority: 80
    conditions:
      intent.parameters.user_input:
        contains: "compensat"
    action: ESCALATE
    reason: Compensation request - requires human review

  # Unverifiable real-time facts restrict
  - name: unverified_realtime_facts
    priority: 70
    conditions:
      evidence.facts.verifiable:
        is_false: true
      evidence.facts.requires_realtime:
        is_true: true
    action: RESTRICT
    reason: Requires real-time facts but they are not verifiable

  # Financial impact escalates
  - name: financial_impact
    priority: 60
    conditions:
      evidence.topic.has_financial_impact:
        is_true: true
    action: ESCALATE
    reason: Financial responsibility - requires human review

metadata:
  version: "1.0.0"
  author: "Governance Team"
```

## Rule Evaluation Order

Rules are evaluated in this order:

1. **Policy rules** (by priority, highest first)
2. **FactVerifiabilityGate**
3. **UncertaintyGate**
4. **ResponsibilityGate**

The first action with the highest precedence wins.
