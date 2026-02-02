# Case Law Library

This directory contains canonical "case law" examples demonstrating governance decisions across various failure modes.

## Philosophy

These cases serve as reference implementations for how the governance gate should behave in specific scenarios. Each case is:

- **Deterministic**: Same input always produces the same decision
- **Documented**: Includes clear rationale for the decision
- **Tested**: Verified with end-to-end tests
- **Reusable**: Can be used as templates for custom policies

## Case Categories

### Information Quality Failures
| Case | Failure Mode | Decision | Key Issue |
|------|--------------|----------|-----------|
| [001_unverifiable_facts](cases/001_unverifiable_facts/) | Unverifiable Facts | RESTRICT | Facts cannot be verified |
| [002_outdated_knowledge](cases/002_outdated_knowledge/) | Outdated Policy | RESTRICT | Knowledge base is stale |
| [003_conflicting_retrieval](cases/003_conflicting_retrieval/) | Tool Conflict | RESTRICT | Retrieval has conflicts |
| [004_low_confidence](cases/004_low_confidence/) | Low Confidence | RESTRICT | Intent/recall confidence low |

### Responsibility Boundary Failures
| Case | Failure Mode | Decision | Key Issue |
|------|--------------|----------|-----------|
| [005_financial_commitment](cases/005_financial_commitment/) | Over-commitment | ESCALATE | Financial responsibility |
| [006_authority_exceeded](cases/006_authority_exceeded/) | Permission Denied | ESCALATE | Requires organizational authority |
| [007_irreversible_action](cases/007_irreversible_action/) | Irreversible | ESCALATE | Cannot undo the action |
| [008_sensitive_topic](cases/008_sensitive_topic/) | Sensitive Topic | ESCALATE | Legal/medical/regulatory |

### Safety & Compliance Failures
| Case | Failure Mode | Decision | Key Issue |
|------|--------------|----------|-----------|
| [009_regulatory_compliance](cases/009_regulatory_compliance/) | Compliance Risk | STOP | Regulatory boundary |
| [010_harmful_content](cases/010_harmful_content/) | Safety Risk | STOP | Potential harm |

## Running Tests

```bash
# Run all case law tests
PYTHONPATH=../../src python -m pytest tests/ -v

# Run specific case test
PYTHONPATH=../../src python -m pytest tests/test_case_001_unverifiable_facts.py -v

# Run case using CLI
govgate eval cases/001_unverifiable_facts/input.json --policy ../../policies/presets/customer_support.yaml
```

## Case File Structure

Each case follows this structure:

```
cases/XXX_case_name/
├── input.json          # Input (intent, context, evidence)
├── expected.json       # Expected decision and rationale
└── README.md           # Case description
```

## Input Format

```json
{
  "intent": {
    "name": "intent_name",
    "confidence": 0.95,
    "parameters": {"key": "value"}
  },
  "context": {
    "user_id": "user_123",
    "channel": "web",
    "session_id": "session_456"
  },
  "evidence": {
    "facts": {...},
    "rag": {...},
    "topic": {...}
  }
}
```

## Expected Output Format

```json
{
  "action": "ALLOW|RESTRICT|ESCALATE|STOP",
  "rationale_substring": "key phrase in rationale",
  "description": "Human-readable explanation"
}
```

## Contributing New Cases

When adding new cases:

1. Follow the naming convention: `XXX_descriptive_name`
2. Include all three files (input.json, expected.json, README.md)
3. Add a corresponding test in `tests/test_case_XXX_*`
4. Update this README with the new case
5. Ensure the case is deterministic (no random values)

## Decision Precedence

When multiple failure modes are present, decisions follow precedence:

```
STOP > ESCALATE > RESTRICT > ALLOW
```

Examples:
- Unverifiable facts + Financial impact → **ESCALATE** (financial wins)
- Conflicting retrieval + Low confidence → **RESTRICT** (both same level)
- Sensitive topic + Irreversible → **ESCALATE** (both same level)
- Regulatory issue + Anything → **STOP** (highest precedence)
