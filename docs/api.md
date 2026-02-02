# HTTP Decision API

Framework-agnostic REST API for evaluating governance decisions.

## Quick Start

```bash
# Install API dependencies
pip install -e ".[api]"

# Start the server
uvicorn governance_gate.api.main:app --reload

# Or use the CLI
govgate serve
```

The API will be available at `http://localhost:8000`

## Endpoints

### POST /decision

Evaluate a governance decision.

**Request:**
```json
{
  "intent": {
    "name": "order_status_query",
    "confidence": 0.95,
    "parameters": {"order_id": "12345"}
  },
  "context": {
    "user_id": "user_123",
    "channel": "web",
    "session_id": "session_456"
  },
  "evidence": {
    "facts": {
      "verifiable": true,
      "verifiable_confidence": 0.9,
      "source": "database"
    },
    "rag": {
      "confidence": 0.85,
      "has_conflicts": false
    },
    "topic": {
      "has_financial_impact": false
    }
  },
  "policy_path": "customer_support.yaml"
}
```

**Response:**
```json
{
  "action": "ALLOW",
  "rationale": "All gates passed - safe to proceed",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "policy_version": "1.0",
  "policy_name": "customer_support_triage",
  "decision_code": "GOVERNANCE_ALLOW",
  "gate_decisions": {
    "fact_verifiability": {
      "gate_name": "fact_verifiability",
      "suggested_action": null,
      "rationale": "Facts are verifiable (confidence: 0.90, source: database)",
      "config_used": null,
      "input_summary": null
    },
    "uncertainty": {...},
    "responsibility": {...}
  },
  "evidence_summary": {...},
  "required_steps": [],
  "timestamp": "2025-01-01T12:00:00.000000Z"
}
```

### POST /validate_policy

Validate a policy file.

**Request:**
```json
{
  "policy_path": "customer_support.yaml"
}
```

**Response:**
```json
{
  "valid": true,
  "policy_name": "customer_support_triage",
  "version": "1.0",
  "rule_count": 8,
  "gates_configured": ["fact_verifiability", "uncertainty", "responsibility"],
  "errors": [],
  "warnings": []
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "policy_base_dir": "/path/to/policies/presets"
}
```

## cURL Examples

```bash
# Evaluate decision
curl -X POST http://localhost:8000/decision \
  -H "Content-Type: application/json" \
  -d '{
    "intent": {"name": "order_status_query", "confidence": 0.95},
    "context": {"channel": "web"},
    "evidence": {
      "facts": {"verifiable": true},
      "rag": {"confidence": 0.85},
      "topic": {"has_financial_impact": false}
    }
  }'

# Validate policy
curl -X POST http://localhost:8000/validate_policy \
  -H "Content-Type: application/json" \
  -d '{"policy_path": "customer_support.yaml"}'

# Health check
curl http://localhost:8000/health
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GOVGATE_POLICY_DIR` | `./policies/presets` | Base directory for policy files |

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `action` | string | ALLOW, RESTRICT, ESCALATE, or STOP |
| `rationale` | string | Human-readable explanation |
| `trace_id` | string | UUID for audit/traceability |
| `policy_version` | string | Policy version (if policy used) |
| `policy_name` | string | Policy name (if policy used) |
| `decision_code` | string | Machine-readable code for aggregation |
| `gate_decisions` | object | Per-gate decision details |
| `evidence_summary` | object | Summary of evidence considered |
| `required_steps` | array | Required next steps |
| `timestamp` | string | ISO 8601 timestamp |

## Integration Examples

### Python (requests)

```python
import requests

response = requests.post(
    "http://localhost:8000/decision",
    json={
        "intent": {"name": "order_status_query", "confidence": 0.95},
        "context": {"channel": "web"},
        "evidence": {
            "facts": {"verifiable": True},
            "rag": {"confidence": 0.85},
            "topic": {"has_financial_impact": False}
        }
    }
)

decision = response.json()
if decision["action"] == "ALLOW":
    # Proceed with execution
    pass
elif decision["action"] == "ESCALATE":
    # Request human review
    pass
```

### JavaScript (fetch)

```javascript
const response = await fetch('http://localhost:8000/decision', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    intent: {name: 'order_status_query', confidence: 0.95},
    context: {channel: 'web'},
    evidence: {
      facts: {verifiable: true},
      rag: {confidence: 0.85},
      topic: {has_financial_impact: false}
    }
  })
});

const decision = await response.json();
console.log(decision.action); // ALLOW, RESTRICT, ESCALATE, or STOP
```

### Go (net/http)

```go
import (
    "bytes"
    "encoding/json"
    "net/http"
)

type GovernanceRequest struct {
    Intent   IntentRequest `json:"intent"`
    Context  ContextRequest `json:"context"`
    Evidence EvidenceRequest `json:"evidence"`
}

func EvaluateDecision(req GovernanceRequest) (*DecisionResponse, error) {
    body, _ := json.Marshal(req)
    resp, err := http.Post(
        "http://localhost:8000/decision",
        "application/json",
        bytes.NewBuffer(body),
    )
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    var decision DecisionResponse
    json.NewDecoder(resp.Body).Decode(&decision)
    return &decision, nil
}
```

## Error Responses

All errors return JSON with an `error` field:

```json
{
  "error": "Policy error: Policy file not found: ..."
}
```

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad request (e.g., invalid policy) |
| 422 | Validation error (malformed request) |
| 500 | Internal server error |
