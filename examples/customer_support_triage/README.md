# Customer Support Triage Examples

This directory demonstrates the core principle of the governance gate:

**Same intent, different outcomes based on context and evidence.**

All three cases use the same intent (`order_status_query`) but produce different decisions:

- **case_01_allow**: User asks how to check order status → ALLOW (rule explanation only)
- **case_02_restrict**: User asks why order hasn't shipped → RESTRICT (depends on real-time facts)
- **case_03_escalate**: User demands compensation → ESCALATE (financial responsibility)

## Running the Examples

```bash
# Evaluate case 01 (ALLOW)
govgate eval cases/case_01_allow/input.json --policy ../../../policies/presets/customer_support.yaml

# Evaluate case 02 (RESTRICT)
govgate eval cases/case_02_restrict/input.json --policy ../../../policies/presets/customer_support.yaml

# Evaluate case 03 (ESCALATE)
govgate eval cases/case_03_escalate/input.json --policy ../../../policies/presets/customer_support.yaml
```

## Expected Results

| Case | Action | Key Rationale |
|------|--------|---------------|
| case_01_allow | ALLOW | Facts are verifiable, uncertainty is acceptable, within responsibility |
| case_02_restrict | RESTRICT | Requires real-time facts but facts are not verifiable |
| case_03_escalate | ESCALATE | Financial responsibility detected |

## Case Law Philosophy

These examples serve as "case law" for the governance system. They demonstrate:

1. **Intent is not destiny**: The same intent can lead to different outcomes
2. **Context matters**: Evidence and context determine the final decision
3. **Deterministic behavior**: Given the same input, the system produces the same output
4. **Clear rationale**: Each decision includes human-readable explanation

Use these as reference when designing your own governance policies.
