# Release Notes

## v0.1.0 - Initial Release (2025-02-02)

**Agent Governance Gate** - Framework-agnostic governance layer for Agent systems.

### Core Features

**1. Deterministic Decision Pipeline**
- Four gates: Safety, Fact Verifiability, Uncertainty, Responsibility
- Clear precedence: STOP > ESCALATE > RESTRICT > ALLOW
- Full traceability with decision codes and audit trails

**2. HTTP Decision API**
- `POST /decision` - Evaluate governance decisions
- `POST /validate_policy` - Validate policy YAML files
- FastAPI-based, production-ready

**3. Case Law Library (12 Cases)**
- 4 RESTRICT cases (unverifiable facts, outdated knowledge, conflicting retrieval, low confidence)
- 6 ESCALATE cases (financial, authority, irreversible, sensitive topics, regulatory compliance)
- 2 STOP cases (fraud detection, restricted content)
- 100% deterministic with unique trace IDs

**4. Structured Gate Authority**
- `final_gate` field explicitly answers "who blocked?"
- No ambiguity - single field identifies the deciding gate
- Full audit trail with `gate_decisions`, `config_used`, `input_summary`

### Integration

**CLI Usage:**
```bash
govgate eval case.json --policy policy.yaml
```

**HTTP API:**
```bash
govgate serve --port 8000
curl http://localhost:8000/decision
```

**Python API:**
```python
from governance_gate.core.pipeline import GovernancePipeline
from governance_gate.gates import SafetyGate, ResponsibilityGate

pipeline = GovernancePipeline(gates=[SafetyGate(), ResponsibilityGate()])
decision = pipeline.evaluate(intent, context, evidence)
# decision.final_gate  # ← "who blocked?"
```

### Test Coverage

- 42 core tests (unit, integration, API)
- 17 case law tests (12 cases + 5 meta tests)
- 4 new structural tests (final_gate correctness)
- **Total: 63 tests, 100% passing**

### Documentation

- [README.md](README.md) - Overview and quickstart
- [docs/overview.md](docs/overview.md) - Architecture deep dive
- [docs/policy_language.md](docs/policy_language.md) - Policy YAML syntax
- [examples/case_law/CASE_SUMMARY.md](examples/case_law/CASE_SUMMARY.md) - Case law reference

### Scope & Non-goals

**In Scope:**
- Governance decisions (ALLOW/RESTRICT/ESCALATE/STOP)
- Deterministic, auditable decision logic
- Policy-driven rule evaluation
- Framework-agnostic integration

**Out of Scope:**
- Workflow engine
- Rule engine (we use YAML policies)
- LLM agent framework (we integrate with any)
- Tool execution (we govern before tool calls)

### Installation

```bash
# Core library
pip install -e .

# With HTTP API
pip install -e ".[api]"

# Verify installation
govgate --version
```

### What's Next

Looking for real-world validation scenarios:
- Customer support triage (refunds, complaints, policy changes)
- Sales support (quotations, commitments, contract terms)
- Knowledge base governance (policy versions, fact verification)

**Contact for integration:** [Your Contact Info]

---

**Full Changelog:** https://github.com/yourusername/agent-governance-gate/commits/v0.1.0
