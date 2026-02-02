# LangGraph Integration Example

This example demonstrates how to integrate the **Governance Gate** into a LangGraph agent flow.

## Architecture

```
User Input
  → Intent Recognition (mock LLM)
    → Governance Gate (this integration)
      → Decision: ALLOW/RESTRICT/ESCALATE/STOP
        → Tool Execution (if ALLOW)
          → Response
```

## Key Concepts

### 1. State Adapter
Converts LangGraph state to Governance Gate types (Intent, Context, Evidence).

### 2. Governance Node
A LangGraph node that:
- Converts state to gate input
- Evaluates the governance decision
- Routes to appropriate next step based on action

### 3. Conditional Routing
Uses LangGraph's conditional edges to route based on decision action:
- **ALLOW** → Continue to tool execution
- **RESTRICT** → Return constrained response
- **ESCALATE** → Return escalation message
- **STOP** → Return stop message

## Quick Start (Without LangGraph)

Verify the adapter logic works without installing LangGraph:

```bash
python verify_without_langgraph.py
```

This tests:
- State conversion (LangGraph ↔ Governance)
- Decision evaluation (ALLOW/RESTRICT/ESCALATE)
- Routing logic based on decisions

## Running the Full Example

```bash
# Install dependencies
pip install langgraph langchain-core

# Run the example
python langgraph_agent.py
```

Expected output:
```
================================================================================
Case 1: ALLOW - How to check order status
================================================================================
User Input: How do I check my order status?
Expected: ALLOW

Actual Action: ALLOW
Trace ID: 550e8400-e29b-41d4-a716-446655440000

RESPONSE:
To check your order status:
1. Go to myaccount.com/orders
2. Enter your order number
3. View real-time status

✓ PASS: Expected ALLOW, got ALLOW

================================================================================
Case 2: RESTRICT - Why order not shipped
================================================================================
...
```

## Testing

### Run Integration Tests

```bash
# From the langgraph_integration directory
PYTHONPATH=../../src python -m pytest tests/ -v
```

Tests cover:
- ✓ STOP prevents tool execution
- ✓ ESCALATE prevents tool execution
- ✓ ALLOW proceeds to tool execution
- ✓ RESTRICT prevents tool execution
- ✓ Decisions are deterministic (same input = same output)
- ✓ State conversion works correctly
- ✓ Routing works correctly

### Test Results

```
============================= test session starts ==============================
collected 16 items

tests/test_integration.py ................                               [100%]

============================== 16 passed in 0.28s ===============================
```

## Files

| File | Purpose |
|------|---------|
| [adapter.py](adapter.py) | Converts LangGraph state ↔ Governance types |
| [langgraph_agent.py](langgraph_agent.py) | Runnable LangGraph agent example |
| [verify_without_langgraph.py](verify_without_langgraph.py) | Verify adapter without LangGraph |
| [tests/test_integration.py](tests/test_integration.py) | Integration tests |

## Example: Same Intent, Different Decisions

The example demonstrates how the **same intent** leads to **different outcomes** based on evidence:

| User Input | Intent | Decision | Reason |
|------------|--------|----------|--------|
| "How do I check my order status?" | order_status_query | **ALLOW** | Facts verifiable, no financial impact |
| "Why has my order not shipped yet?" | order_status_query | **RESTRICT** | Requires real-time facts that are unverifiable |
| "You should compensate me" | order_status_query | **ESCALATE** | Financial responsibility detected |

## Integration Pattern

```python
from adapter import LangGraphGovernanceAdapter, create_customer_support_adapter

# 1. Create adapter with policy
adapter = create_customer_support_adapter()

# 2. Build LangGraph graph
from langgraph.graph import StateGraph, END

workflow = StateGraph(AgentState)
workflow.add_node("governance_gate", lambda s: adapter.evaluate_governance(s))
workflow.add_node("execute_tools", execute_tools_function)
# ... add other nodes

# 3. Add conditional routing based on decision
workflow.add_conditional_edges(
    "governance_gate",
    adapter.route_based_on_decision,
    {
        "execute_tools": "execute_tools",
        "respond_restricted": "respond_restricted",
        "respond_escalate": "respond_escalate",
        "respond_stop": "respond_stop",
    },
)

# 4. Compile and run
graph = workflow.compile()
result = graph.invoke(initial_state)
```

## Key Features

1. **No LLM Calls**: The example uses mock intent recognition (keyword-based) to demonstrate governance without requiring an LLM

2. **Deterministic Behavior**: Given the same input, the system produces the same decision every time

3. **Clear Separation**: Governance is a separate concern from intent recognition and tool execution

4. **Auditable Decisions**: Every decision includes a trace_id and rationale

5. **Extensible**: Easy to add new gates, modify routing logic, or customize responses
