# Case Law Summary

Quick reference for all 12 failure-mode cases.

| # | Case | Decision | Trigger |
|---|------|----------|---------|
| 001 | Unverifiable Facts | **RESTRICT** | Facts not verifiable + requires realtime |
| 002 | Outdated Knowledge | **RESTRICT** | KB 45 days old (threshold: 30) |
| 003 | Conflicting Retrieval | **RESTRICT** | 3 conflicting retrieval results |
| 004 | Low Confidence | **RESTRICT** | Intent 0.55, RAG 0.5 (both low) |
| 005 | Financial Commitment | **ESCALATE** | Discount request = financial impact |
| 006 | Authority Exceeded | **ESCALATE** | Policy change = requires authority |
| 007 | Irreversible Action | **ESCALATE** | Account closure = irreversible |
| 008 | Sensitive Topic | **ESCALATE** | Legal action = sensitive + financial |
| 009 | Regulatory Compliance | **ESCALATE** | Medical advice = sensitive topic |
| 010 | Harmful Content | **ESCALATE** | Payment bypass = financial (escalated) |
| 011 | Fraud Detection | **STOP** | Explicit payment bypass/fraud request |
| 012 | Restricted Content | **STOP** | Age-restricted purchase without ID |

## Decision Distribution

- **RESTRICT**: 4 cases (33%)
- **ESCALATE**: 6 cases (50%)
- **STOP**: 2 cases (17%)
- **ALLOW**: 0 cases (0%)

## Running All Cases

```bash
# Run all tests
cd examples/case_law
PYTHONPATH=../../src python -m pytest tests/ -v

# Test individual case with CLI
govgate eval cases/001_unverifiable_facts/input.json --policy ../../policies/presets/customer_support.yaml

# Test determinism (run same case 3x)
for i in 1 2 3; do
  govgate eval cases/001_unverifiable_facts/input.json --policy ../../policies/presets/customer_support.yaml | grep '"action"'
done
# All should return the same action
```

## Test Results

```
============================= test session starts ==============================
collected 15 items

test_case_law.py ...............                               [100%]

============================== 15 passed in 0.06s ===============================
```

All cases:
- ✓ Produce deterministic decisions
- ✓ Include unique trace IDs
- ✓ Have gate contributions from all 3 gates
- ✓ Include human-readable rationale
