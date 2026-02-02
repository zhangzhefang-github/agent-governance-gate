# Starter Kits

Production-ready templates for integrating governance gate into specific scenarios.

## Available Kits

### Customer Support
**Path:** [customer_support/](customer_support/)

**Use Case:** Customer support triage, handling refunds, policy questions, complaints

**Includes:**
- Policy YAML with financial/authority/sensitive intent rules
- 10 case templates (refunds, policy changes, legal threats, fraud)
- Python integration example with timeout handling
- Metrics definition with KPIs and alert thresholds
- 4-week optimization roadmap

**Expected Outcomes:**
- Reduce escalations by 5-10%
- Block >95% of fraud attempts
- 100% audit trail for all decisions

## How to Use a Starter Kit

### 1. Choose Your Scenario

If you're doing customer support → Use `customer_support/`
If you're doing sales operations → Coming soon
If you're doing knowledge base → Coming soon

### 2. Customize the Policy

Each kit includes a `policy.yaml` with business rules. Edit to match:

- Your intent names
- Your risk thresholds
- Your data availability
- Your escalation criteria

### 3. Fill Case Templates

Each kit has `cases/` with JSON skeletons:

```json
{
  "intent": {
    "name": "YOUR_INTENT",
    "confidence": 0.0  // TODO: Set actual value
  },
  "evidence": {
    "facts": {
      "verifiable": true  // TODO: Adjust
    }
  }
}
```

Replace `0.0` and `TODO` with real data from your system.

### 4. Integrate Using the Example

Copy the integration example (`integration_example.py`) and:

1. Set your API endpoint
2. Implement your agent logic
3. Add your logging system
4. Deploy to production

### 5. Track Metrics

Each kit includes `metrics/definitions.md` with:

- Recommended metrics to collect
- KPI targets
- Alert thresholds
- Dashboard examples

## Creating Your Own Starter Kit

If none of the existing kits match your scenario, create a new one:

### Directory Structure

```
your_scenario/
├── policy.yaml          # Business rules
├── cases/               # 10 case templates
├── integration_example.py
├── metrics/
│   └── definitions.md
└── README.md
```

### Checklist

- [ ] Policy covers your main risk dimensions
- [ ] Cases cover common scenarios (allow + restrict + escalate + stop)
- [ ] Integration example handles all 4 decision types
- [ ] Metrics include business KPIs (not just technical)
- [ ] README has customization guide

## Contributing

Have a starter kit to share?

1. Create a directory following the structure above
2. Test all cases with: `govgate eval cases/*.json --policy policy.yaml`
3. Include real-world examples (use synthetic data, but realistic)
4. Submit a PR

## Questions?

- **Main Documentation:** [../README.md](../README.md)
- **Integration Guide:** [../docs/integration.md](../docs/integration.md)
- **Issues:** https://github.com/zhangzhefang-github/agent-governance-gate/issues
