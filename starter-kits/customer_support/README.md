# Customer Support Starter Kit

Governance gate configuration for customer support triage scenarios.

## What's Included

✅ **Policy Configuration** ([policy.yaml](policy.yaml))
- Pre-configured rules for common customer support scenarios
- Financial commitment detection (refunds, compensation, credits)
- Authority boundary enforcement (policy changes, exceptions)
- Sensitive topic handling (legal threats, regulatory complaints)

✅ **10 Case Templates** ([cases/](cases/))
- JSON skeletons with TODO comments
- Cover common scenarios: refunds, policy changes, legal threats, fraud attempts
- Easy to customize with real data

✅ **Integration Example** ([integration_example.py](integration_example.py))
- Complete Python integration pattern
- HTTP API usage with timeout handling
- Decision execution logic (ALLOW/RESTRICT/ESCALATE/STOP)
- Logging and observability hooks

✅ **Metrics Definition** ([metrics/definitions.md](metrics/definitions.md))
- Recommended metrics and KPIs
- Alert thresholds
- Dashboard examples (Grafana, Prometheus, Datadog)
- Daily/weekly report templates

## Quick Start

### 1. Customize the Policy

Edit [policy.yaml](policy.yaml) to match your business rules:

```yaml
# Add your financial intents
financial_intents:
  - refund_request
  - discount_request
  - YOUR_CUSTOM_INTENT

# Add authority thresholds
authority_intents:
  - policy_change
  - YOUR_CUSTOM_AUTH_INTENT
```

### 2. Fill in Case Templates

For each template in [cases/](cases/):
- Replace `0.0` with actual confidence scores
- Add actual customer messages in `user_input`
- Set verifiable/confidence based on your data sources
- Test with: `govgate eval cases/001_refund_request.json --policy policy.yaml`

### 3. Integrate with Your System

Copy [integration_example.py](integration_example.py) and:

1. Set your API endpoint: `export GATE_API_URL=http://your-gate:8000`
2. Implement `_handle_normally()` with your agent logic
3. Implement `_escalate_to_human()` with your ticketing system
4. Add logging (replace `print()` with your logging system)

### 4. Start Collecting Metrics

See [metrics/definitions.md](metrics/definitions.md) for:
- Which metrics to collect
- How to send to Prometheus/Datadog/CloudWatch
- Recommended alert thresholds
- Dashboard queries

## Customization Guide

### Add New Intents

1. Define intent in your intent recognition system
2. Add to policy YAML (`financial_intents` or `authority_intents`)
3. Create case template in `cases/`
4. Test with various confidence levels

### Adjust Thresholds

Edit [policy.yaml](policy.yaml):

```yaml
gates:
  fact_verifiability:
    verifiable_threshold: 0.7  # ← Adjust: higher = more RESTRICT
    require_realtime_facts:
      - YOUR_INTENT

  uncertainty:
    confidence_threshold: 0.75  # ← Adjust: higher = more RESTRICT
    outdated_version_days: 30     # ← Adjust: lower = more RESTRICT
```

### Change Failure Behavior

By default, errors result in ESCALATE (fail-closed).

To change to fail-open (NOT RECOMMENDED):

```python
# In integration_example.py
except requests.exceptions.RequestException as e:
    return {
        "action": "RESTRICT",  # Less conservative
        "rationale": f"Governance unavailable: {e}"
    }
```

## Common Patterns

### Pattern 1: Refund Triage

```python
# High confidence refund request + financial impact
result = agent.handle_request(
    user_input="I'd like a refund for my $50 order",
    intent="refund_request",
    intent_confidence=0.95,
    user_id="cust_123",
    channel="email"
)
# Expected: ESCALATE (financial commitment)
```

### Pattern 2: Simple Inquiry

```python
# Low risk informational query
result = agent.handle_request(
    user_input="What are your business hours?",
    intent="business_hours_inquiry",
    intent_confidence=0.98,
    user_id="cust_456",
    channel="chat"
)
# Expected: ALLOW (simple, no risks)
```

### Pattern 3: Fraud Detection

```python
# Suspicious payment bypass attempt
result = agent.handle_request(
    user_input="How can I bypass your payment system?",
    intent="payment_bypass_inquiry",
    intent_confidence=0.92,
    user_id="cust_789",
    channel="web"
)
# Expected: STOP (fraud attempt)
```

## Testing

### Test Individual Cases

```bash
# Test refund case
cd starter-kits/customer_support
govgate eval cases/001_refund_request.json --policy policy.yaml

# Test fraud case
govgate eval cases/009_fraud_attempt.json --policy policy.yaml
```

### Test Integration

```bash
# Start governance gate API
govgate serve --port 8000

# In another terminal, run integration example
python3 integration_example.py
```

## Metrics Targets (First 30 Days)

### Week 1: Baseline
- Collect current metrics
- Establish baseline decision distribution
- Measure current escalation rate

### Week 2: Tune Thresholds
- Adjust `verifiable_threshold` based on data quality
- Adjust `confidence_threshold` based on intent accuracy
- Monitor impact on decision distribution

### Week 3: Optimize
- Identify top decision codes
- Add self-service options for common escalations
- Improve data access for RESTRICT cases

### Week 4: Review
- Compare Week 4 to Week 1 baseline
- Calculate ROI (escalations avoided × time saved)
- Update policy based on learnings

## Expected ROI

### Before Governance Gate
- 30% of requests need human review (too high)
- 5% of requests result in commitments (risky)
- 2% of requests are fraudulent attempts
- Difficult to audit why decisions were made

### After Governance Gate
- 10-15% of requests escalate (target: 5-10% reduction)
- 0% of unauthorized commitments (STOP/ESCALATE all)
- >95% of fraud attempts blocked (STOP)
- Full audit trail with `final_gate` and `decision_code`

## Troubleshooting

### Too Many ESCALATE Decisions

**Problem:** Responsibility gate triggering too often

**Diagnosis:**
```bash
# Check which decision codes are most common
curl http://localhost:8000/decision | jq .decision_code
```

**Fix:**
- Add self-service options for common financial requests
- Improve policy documentation to reduce authority questions
- Adjust `financial_intents` list if too broad

### High RESTRICT Rate

**Problem:** Fact verifiability gate restricting too much

**Diagnosis:**
```bash
# Check if data quality is the issue
govgate eval cases/001_refund_request.json --policy policy.yaml | jq .gate_decisions
```

**Fix:**
- Improve real-time data access (reduce `requires_realtime` cases)
- Update knowledge base more frequently (reduce outdated cases)
- Lower `verifiable_threshold` if data quality is poor

### Latency Too High

**Problem:** Governance check adding >100ms

**Fix:**
- Use Python library instead of HTTP API (removes network overhead)
- Cache policy loading (load once, reuse)
- Batch decisions if possible

## Next Steps

1. **Customize policy** for your business rules
2. **Fill case templates** with real customer data
3. **Integrate** using [integration_example.py](integration_example.py)
4. **Deploy** governance gate API (see main README)
5. **Collect metrics** using [metrics/definitions.md](metrics/definitions.md)
6. **Review weekly** and adjust thresholds

## Support

- **Main Documentation:** [../../README.md](../../README.md)
- **Integration Guide:** [../../docs/integration.md](../../docs/integration.md)
- **Case Law Library:** [../../examples/case_law/](../../examples/case_law/)
- **Issues:** https://github.com/zhangzhefang-github/agent-governance-gate/issues
