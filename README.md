# agent-governance-gate

[English](README.md) | [简体中文](README_zh.md)

A governance gate for Agent systems that decides whether an action is allowed, restricted, escalated, or stopped,
based on risk and responsibility, not just intent.

This project focuses on engineering control for probabilistic AI systems,
not on model capability, prompt design, or user experience optimization.

---

## Quickstart (2 minutes)

### Install

```bash
# Core library
pip install -e .

# With HTTP API
pip install -e ".[api]"

# Verify
govgate --version
```

### Try a Case

```bash
# Run a fraud detection case (returns STOP with final_gate="safety")
cd examples/case_law
PYTHONPATH=../../src govgate eval cases/011_fraud_detection/input.json \
  --policy ../../policies/presets/customer_support.yaml
```

Output:
```json
{
  "action": "STOP",
  "final_gate": "safety",
  "rationale": "Fraud request detected: 'payment system' - Refusing to process...",
  "trace_id": "ff69b873-7b5a-4bc1-a18e-d0814a87cacb"
}
```

### Start HTTP API

```bash
# Start server
govgate serve --port 8000

# In another terminal, test it
curl -X POST http://localhost:8000/decision \
  -H "Content-Type: application/json" \
  -d '{
    "intent": {"name": "test", "confidence": 0.9},
    "context": {},
    "evidence": {}
  }'
```

### Integration (Python)

```python
from governance_gate.core.pipeline import GovernancePipeline
from governance_gate.gates import SafetyGate, ResponsibilityGate
from governance_gate.core.types import Intent, Context, Evidence

pipeline = GovernancePipeline(gates=[SafetyGate(), ResponsibilityGate()])
decision = pipeline.evaluate(intent, context, evidence)

print(f"Decision: {decision.action}")        # ALLOW/RESTRICT/ESCALATE/STOP
print(f"Who blocked: {decision.final_gate}")  # "safety", "responsibility", etc.
```

---

## Why this project exists

Modern Agent and RAG systems are probabilistic by nature.

Even with high intent recognition accuracy, systems still fail in production because:

- They answer questions that depend on unverifiable or outdated facts
- They continue execution under uncertainty
- They cross responsibility boundaries (commitments, money, authority)
- Failures are not explicit, not traceable, and not stoppable

Most implementations attempt to solve these issues by:

- Improving model accuracy
- Adding prompts or heuristics
- Tuning retrieval strategies

This project takes a different stance:

These failures are not model problems.
They are governance problems.

---

## What this project is and is not

This project is:

- A governance layer for Agent systems
- A decision gate placed after intent recognition
- A mechanism to make non-action an explicit system decision
- A reusable engineering skeleton for risk and responsibility control

This project is not:

- Another Agent implementation
- A chatbot or demo application
- A prompt engineering framework
- A business workflow engine

---

## Core idea

Intent recognition answers the question:

What does the user want to do?

Governance answers a different question:

Is the system allowed to do this now?

These are fundamentally different questions.

This project treats governance as a first-class engineering concern.

---

## Decision pipeline

User Input
  ->
Intent Recognition (language understanding)
  ->
Risk and Responsibility Gate (this project)
  ->
ALLOW / RESTRICT / ESCALATE / STOP
  ->
Agent Execution (if allowed)

Intent recognition may be probabilistic.
Responsibility boundaries must be deterministic.

---

## Governance principles

The gate evaluates a request using three orthogonal dimensions.

### 1. Fact verifiability

- Does the response depend on current or external facts
- Are those facts available, authoritative, and trusted
- Is the system authorized to access them

If facts cannot be verified, the system must not conclude.

---

### 2. Uncertainty exposure

- Is retrieval confidence low
- Are multiple tools producing conflicting results
- Is the knowledge version outdated or incomplete

Uncertainty must never be silently absorbed.

---

### 3. Responsibility boundary

- Would the response be interpreted as an organizational commitment
- Does it affect money, authority, or irreversible decisions
- Is human judgment required by policy or regulation

If responsibility is involved, the system must not decide.

---

## Decision outcomes

The governance gate always produces an explicit decision.

ALLOW
  Safe to proceed autonomously

RESTRICT
  Respond with constraints, disclaimers, or suggestions only

ESCALATE
  Require human review or approval

STOP
  Do not continue due to insufficient authority or information

Each decision includes:

- The reasoning behind the decision
- Evidence used to support the decision
- A trace identifier for auditability

---

## Example: same intent, different outcomes

Intent: order_status_query

User question:
How do I check my order status?
Decision:
ALLOW
Reason:
Rule explanation only

User question:
Why has my order not shipped yet?
Decision:
RESTRICT
Reason:
Depends on real-time facts

User question:
You messed up, you should compensate me
Decision:
ESCALATE
Reason:
Financial responsibility

Intent does not change.
Risk and responsibility do.

---

## Integration philosophy

This gate is framework agnostic.

It can be embedded into:

- LangGraph-based agent flows
- Dify workflows
- Custom agent pipelines
- API-based AI services

The gate does not care how intents are produced.
It does not execute actions.

It only decides whether execution is allowed.

---

## Project status

This repository provides:

- A minimal governance decision engine
- Policy-driven risk rules
- Canonical failure cases
- Deterministic decision behavior

It intentionally avoids:

- Domain-specific business logic
- Model optimization
- UI or product features

The goal is engineering clarity, not completeness.

---

## Who this is for

This project is intended for engineers and architects who:

- Build production-grade Agent or RAG systems
- Are responsible for system failures, not just demos
- Design AI systems that must stop safely
- Treat AI as infrastructure, not as a feature

---

## Design philosophy

Probabilistic systems require deterministic responsibility boundaries.

Engineering systems must know when not to act.

---

## Scope & Non-goals

**This project IS:**

✅ Governance gate (ALLOW/RESTRICT/ESCALATE/STOP decisions)
✅ Deterministic, auditable decision logic
✅ Policy-driven rule evaluation (YAML)
✅ Framework-agnostic integration layer
✅ Reference implementation for production systems

**This project is NOT:**

❌ Workflow engine (use LangGraph, Temporal, etc.)
❌ Rule engine (we use simple YAML policies, not Drools/OPA)
❌ LLM agent framework (we integrate with any, not compete)
❌ Tool execution (we govern BEFORE tool calls, not execute)
❌ Database/persistence layer (audit export is optional)
❌ Monitoring/observability platform (we provide decisions, not dashboards)

**Why this distinction matters:**

This project is a **governance primitive**.
It's designed to be embedded into existing systems, not replace them.

If you need:
- Workflow orchestration → Use LangGraph/Dify/Temporal
- Complex rule management → Build on top of our YAML policies
- Full agent platform → Integrate our gate as a pre-execution check
- Monitoring infrastructure → Consume our decision events

**Anti-pattern (don't do this):**
```
❌ "Add feature X to governance gate"
```
Feature creep destroys clarity.

**Correct pattern:**
```
✅ "Use governance gate to protect feature X"
✅ "Consume governance decisions in monitoring system"
✅ "Build policy management UI on top of YAML policies"
```

---

## License

MIT
