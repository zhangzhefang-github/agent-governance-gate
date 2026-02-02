# Audit and Tracing

## Overview

Every governance decision includes a unique `trace_id` that enables full auditability of the decision-making process.

## Decision Output

Each decision contains:

```json
{
  "action": "RESTRICT",
  "rationale": "Intent requires real-time facts but facts are not verifiable | Retrieval confidence 0.85 is acceptable",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "evidence_summary": {
    "intent": "order_status_query",
    "context": {
      "channel": "web",
      "user_id": "user_123"
    },
    "evidence_keys": ["facts", "rag", "topic"]
  },
  "gate_contributions": {
    "fact_verifiability": "Intent 'order_status_query' requires real-time facts but facts are not verifiable",
    "uncertainty": "Uncertainty is acceptable (confidence: 0.85, coverage: 0.95)",
    "responsibility": "Intent 'order_status_query' is within responsibility boundaries"
  },
  "required_steps": [],
  "timestamp": "2025-01-01T12:00:00.000000Z"
}
```

## Trace ID

The `trace_id` is a UUID v4 that uniquely identifies each decision. Use it to:

- Correlate decisions with logs
- Debug why a specific decision was made
- Audit governance decisions over time
- Track decision patterns and trends

## Gate Contributions

Each gate contributes to the final decision:

- **fact_verifiability**: Assesses whether facts can be verified
- **uncertainty**: Assesses whether uncertainty is acceptable
- **responsibility**: Assesses whether responsibility boundaries are respected

## Building Audit Trails

To build a complete audit trail:

1. **Log all decisions** with their trace_id
2. **Store input data** (intent, context, evidence) with trace_id
3. **Record downstream actions** linked to trace_id
4. **Monitor decision patterns** for anomalies

Example:

```python
decision = pipeline.evaluate(intent, context, evidence)

# Log the decision
logger.info(
    "Governance decision",
    extra={
        "trace_id": decision.trace_id,
        "action": decision.action.value,
        "rationale": decision.rationale,
        "intent": intent.name,
        "user_id": context.user_id,
    }
)

# Store for audit
audit_store.record({
    "trace_id": decision.trace_id,
    "timestamp": decision.timestamp,
    "input": {"intent": intent, "context": context, "evidence": evidence},
    "output": decision.to_dict(),
})
```

## Trace Exporters

The audit module includes exporters for different output formats:

```python
from governance_gate.audit import ConsoleExporter, JSONExporter

tracer = AuditTracer()
# ... run pipeline ...

console_exporter = ConsoleExporter()
json_exporter = JSONExporter()

# Export to console
print(console_exporter.export(tracer.get_trace_summary()))

# Export to JSON
json_str = json_exporter.export(tracer.get_trace_summary())
```
