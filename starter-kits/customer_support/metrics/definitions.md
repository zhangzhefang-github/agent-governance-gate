# Customer Support - Metrics & KPIs

Recommended metrics for monitoring governance gate performance in customer support scenarios.

## Core Decision Metrics

### Decision Distribution
```
governance_decisions_total{action="allow",     channel="web"}
governance_decisions_total{action="restrict",  channel="web"}
governance_decisions_total{action="escalate",  channel="web"}
governance_decisions_total{action="stop",      channel="web"}
```

**Target KPIs:**
- **Allow Rate**: 60-80% (most queries should be handled autonomously)
- **Restrict Rate**: 10-20% (some queries need disclaimers)
- **Escalate Rate**: 5-15% (financial/authority issues need humans)
- **Stop Rate**: <5% (fraud/abuse should be very low)

### Alert Thresholds
- ⚠️  Escalate rate >20% for 5min → "Too many escalations, check policy"
- 🚨 Stop rate >10% for 5min → "Possible fraud attack"
- ⚠️  Allow rate <40% for 5min → "Gate too restrictive, check configuration"

## Gate-Specific Metrics

### Final Gate Distribution
```
governance_final_gate_total{gate="safety"}
governance_final_gate_total{gate="responsibility"}
governance_final_gate_total{gate="fact_verifiability"}
governance_final_gate_total{gate="uncertainty"}
```

**Analysis:**
- **High responsibility gate** → Lots of financial/authority requests
  - Consider: Dedicated team for escalations
  - Consider: Self-service options for common requests

- **High fact_verifiability gate** → Data availability issues
  - Action: Improve real-time data access
  - Action: Update knowledge base more frequently

- **High uncertainty gate** → Low confidence in RAG/intent
  - Action: Improve RAG quality
  - Action: Better intent training data

### Safety Gate Spike Detection
```
rate(governance_final_gate_total{gate="safety"}[5m])
  > 3 * rate(governance_final_gate_total{gate="safety"}[1h] offset 1h)
```

**Alert:** "Possible fraud/abuse attack - safety gate blocking rate spiked 3x"

## Decision Code Metrics

### Top Decision Codes
```
# Financial escalations
governance_decision_code_total{code="RESPONSIBILITY_ESCALATE_INTENT"}

# Fraud blocks
governance_decision_code_total{code="SAFETY_STOP_FRAUD"}

# Unverifiable facts
governance_decision_code_total{code="FACTS_RESTRICT_UNVERIFIABLE"}
```

**Actionable insights:**
- Group by `decision_code` to identify **most common failure reasons**
- Top codes indicate **where to invest improvements**

## Performance Metrics

### Latency
```
governance_decision_latency_ms{quantile="0.5"}   # p50: <10ms
governance_decision_latency_ms{quantile="0.95"}  # p95: <50ms
governance_decision_latency_ms{quantile="0.99"}  # p99: <100ms
```

**Alert:**
- ⚠️  p95 >100ms → "Governance check adding too much latency"

### Error Rate
```
governance_errors_total{error_type="policy_load_failed"}
governance_errors_total{error_type="timeout"}
governance_errors_total{error_type="validation_failed"}
```

## Business Impact Metrics

### Escalation Efficiency
```
# Escalations that could have been ALLOWED with better data
escalations_preventable_rate = (
    escalations_due_to_unverifiable_facts / total_escalations
)
```

**Target:** <30% of escalations due to data issues

### Customer Experience
```
# Percentage of requests handled without human intervention
automation_rate = allow_rate / (allow_rate + restrict_rate)
```

**Target:** >70% automation rate

### Fraud Prevention
```
# Fraud attempts blocked (STOP from safety gate)
fraud_blocked_rate = stop_rate_with_gate_safety / total_requests
```

**Target:** >95% of fraud attempts blocked

## Daily/Weekly Reports

### Daily Summary (for ops team)
```
Total requests: 10,000
- ALLOW: 7,500 (75%)
- RESTRICT: 1,500 (15%)
- ESCALATE: 800 (8%)
- STOP: 200 (2%)

Gate breakdown:
- Safety: 2% (fraud)
- Responsibility: 7% (escalated)
- Fact Verifiability: 12% (restricted)
- Uncertainty: 4% (restricted)

Top decision codes:
1. FACTS_RESTRICT_UNVERIFIABLE: 8%
2. RESPONSIBILITY_ESCALATE_INTENT: 6%
3. UNCERTAINTY_RESTRICT_RETRIEVAL: 3%

Performance:
- p50 latency: 8ms
- p95 latency: 35ms
- p99 latency: 78ms
- Error rate: 0.1%
```

### Weekly Trends (for management)
```
Week-over-week changes:
- Automation rate: 72% → 74% (+2% ✅)
- Escalation rate: 9% → 8% (-1% ✅)
- Stop rate: 2.1% → 1.9% (-0.2% ✅)
- Avg latency: 42ms → 38ms (-4ms ✅)

Top improvement opportunities:
1. Unverifiable facts (12% RESTRICT) → improve data access
2. Policy uncertainty (8% RESTRICT) → update knowledge base
3. Financial escalations (6% ESCALATE) → add self-service options
```

## Dashboard Examples

### Grafana Dashboard Queries

**Panel 1: Decision Donut Chart**
```promql
sum by (action) (rate(governance_decisions_total[5m]))
```

**Panel 2: Gate Distribution (Bar)**
```promql
sum by (final_gate) (rate(governance_decisions_total[5m]))
```

**Panel 3: Latency Heatmap**
```promql
rate(governance_decision_latency_ms[5m])
```

**Panel 4: Top 10 Decision Codes**
```promql
topk(10, sum by (decision_code) (rate(governance_decisions_total[1h])))
```

## Integration with Existing Tools

### Send to Prometheus
```python
from prometheus_client import Counter, Histogram

decision_counter = Counter(
    'governance_decisions_total',
    'Governance decisions',
    ['action', 'final_gate', 'channel']
)

# Record decision
decision_counter.labels(
    action=decision['action'],
    final_gate=decision.get('final_gate', 'none'),
    channel=context['channel']
).inc()
```

### Send to Datadog
```python
from datadog import statsd

# Record decision
statsd.increment(
    'governance.decision',
    value=1,
    tags=[
        f"action:{decision['action']}",
        f"gate:{decision.get('final_gate', 'none')}"
    ]
)

# Record latency
statsd.histogram('governance.latency_ms', latency_ms)
```

### Send to CloudWatch
```python
import boto3

cloudwatch = boto3.client('cloudwatch')

cloudwatch.put_metric_data(
    Namespace='GovernanceGate',
    MetricData=[{
        'MetricName': 'DecisionCount',
        'Dimensions': [
            {'Name': 'Action', 'Value': decision['action']},
            {'Name': 'FinalGate', 'Value': decision.get('final_gate', 'none')}
        ],
        'Value': 1,
        'Unit': 'Count'
    }]
)
```

## Review Cadence

**Daily:**
- Check error rate
- Check p95 latency
- Review STOP decisions (verify false positives)

**Weekly:**
- Review gate distribution trends
- Analyze top decision codes
- Identify improvement opportunities

**Monthly:**
- Review and update policy thresholds
- Assess automation rate trends
- Calculate ROI (escalations avoided)
