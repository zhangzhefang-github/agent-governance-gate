# Anti-Patterns: What NOT to Do

**Educational Examples of Dangerous Configurations**

This directory contains examples of **incorrect but tempting** governance configurations. These are anti-patterns that seem reasonable but create serious security, compliance, or responsibility risks.

## Purpose

**These are NOT for production use.** They are educational tools to:
- Learn from common mistakes
- Understand why certain configurations are dangerous
- Recognize anti-patterns in code reviews
- Build intuition for governance design

## How to Use These Examples

For each anti-pattern:
1. **Read the explanation** - Understand why it's dangerous
2. **Compare with the correct approach** - See the right way
3. **Test both configurations** - Observe the behavioral difference
4. **Internalize the principle** - Apply to other scenarios

## Anti-Pattern Catalog

### 1. [overly_permissive_policy.yaml](overly_permissive_policy.yaml)
**The "Anything Goes" Anti-Pattern**

**What it does:** Sets all thresholds to zero, disables all safety checks, allows all intents without restrictions.

**Why it's tempting:** Reduces friction, increases autonomy, fewer escalations.

**Why it's dangerous:**
- ❌ No financial commitment controls → agents can promise unauthorized refunds
- ❌ No authority boundaries → agents can make policy exceptions
- ❌ No fact verification → agents can hallucinate or use outdated info
- ❌ No uncertainty handling → agents can act with low confidence
- ❌ No safety checks → fraud attempts go undetected

**Real-world impact:** Agent promises $500 refund to customer, company loses money, customer trust erodes when refund is later denied.

**Correct approach:** Use [../policy.yaml](../policy.yaml) which sets appropriate thresholds based on risk.

---

### 2. [missing_responsibility_gate.yaml](missing_responsibility_gate.yaml)
**The "No Human Oversight" Anti-Pattern**

**What it does:** Removes the Responsibility gate entirely, allowing financial/authority/sensitive intents to proceed without review.

**Why it's tempting:** Reduces escalations, faster responses, lower operational costs.

**Why it's dangerous:**
- ❌ Financial commitments → unauthorized refunds, credits, adjustments
- ❌ Authority violations → policy exceptions, contract modifications
- ❌ Sensitive topics → legal liability (legal/medical/regulatory advice)

**Real-world impact:** Agent processes $2,000 refund without approval, violates company policy, creates audit compliance issue.

**Correct approach:** Always include Responsibility gate for any domain with:
- Financial impact
- Authority requirements
- Legal/regulatory sensitivity
- Irreversible actions

---

### 3. [blind_trust_confidence.yaml](blind_trust_confidence.yaml)
**The "Trust the AI" Anti-Pattern**

**What it does:** Sets confidence thresholds to 0.1 (essentially disabled), allowing low-confidence intents to proceed.

**Why it's tempting:** Reduces RESTRICT responses, fewer "I don't understand" replies, higher completion rates.

**Why it's dangerous:**
- ❌ Low confidence intent recognition → wrong intent detected
- ❌ Wrong action taken → customer gets incorrect response
- ❌ Hidden failures → no visibility into uncertainty

**Real-world impact:** Intent "refund_request" (confidence 0.3) misclassified as "order_status_query", agent provides order info instead of processing refund, customer frustrated.

**Correct approach:** Set confidence threshold ≥ 0.7 for production, monitor RESTRICT rate for low-confidence patterns.

---

### 4. [disabled_safety_gate.yaml](disabled_safety_gate.yaml)
**The "No Fraud Detection" Anti-Pattern**

**What it does:** Removes Safety gate, disabling fraud/illegal/security keyword detection.

**Why it's tempting:** Removes false positives, allows unrestricted conversations.

**Why it's dangerous:**
- ❌ No fraud detection → payment bypass, account takeover attempts succeed
- ❌ No illegal activity detection → money laundering, illegal requests not flagged
- ❌ No security checks → phishing attempts succeed

**Real-world impact:**
- Customer asks "How do I bypass your payment system?"
- Agent: "Here's how..." (provides actual guidance)
- Security breach, fraud losses, reputational damage

**Correct approach:** Always enable Safety gate, STOP on fraud/illegal/security triggers, review blocked requests.

---

### 5. [no_uncertainty_handling.yaml](no_uncertainty_handling.yaml)
**The "Pretend to Know" Anti-Pattern**

**What it does:** Removes Uncertainty gate, allowing agents to act even when RAG confidence is low or results conflict.

**Why it's tempting:** Fewer "I don't know" responses, higher perceived helpfulness.

**Why it's dangerous:**
- ❌ Low retrieval confidence → hallucinations, incorrect information
- ❌ Conflicting results → inconsistent answers, customer confusion
- ❌ Outdated knowledge base → obsolete policies presented as current

**Real-world impact:**
- Knowledge base outdated (refund policy changed from 30 to 14 days)
- Agent confidently states: "Our refund policy is 30 days"
- Customer relies on outdated info, complaint escalates when refund denied

**Correct approach:** Always enable Uncertainty gate, RESTRICT on low confidence/conflicts, update knowledge base frequently.

---

## Anti-Pattern Detection Checklist

Use this checklist to review your governance configuration:

### Red Flags
- [ ] Any threshold set to 0 or disabled
- [ ] Responsibility gate missing or disabled
- [ ] Safety gate disabled
- [ ] Confidence thresholds < 0.5
- [ ] No STOP actions configured
- [ ] All rules disabled (enabled: false)
- [ ] Empty gate configuration
- [ ] Comment says "TODO: add security"

### Risk Indicators
- [ ] High ALLOW rate (> 90%) with complex intents
- [ ] Zero RESTRICT/ESCALATE/STOP decisions
- [ ] Policy designed to "reduce friction" without safety review
- [ ] No testing with failure scenarios

### Correct Design Principles
✅ **Defense in depth** - Multiple gates for high-risk scenarios
✅ **Fail safe defaults** - ESCALATE when uncertain
✅ **Human in the loop** - Responsibility gate for sensitive actions
✅ **Transparency** - Clear rationales for all decisions
✅ **Auditability** - Trace IDs and decision codes for all actions

## Learning Exercise

**Try this:** Take each anti-pattern and:

1. Load it into the governance gate: `govgate eval anti_patterns/NAME.yaml`
2. Test with a dangerous case (e.g., fraud attempt, financial request)
3. Observe the decision (ALLOW when it should STOP/ESCALATE)
4. Compare with correct policy from `../policy.yaml`
5. Document the difference and why it matters

## Questions?

- **Main Documentation:** [../../README.md](../../README.md)
- **Integration Guide:** [../../docs/integration.md](../../docs/integration.md)
- **Correct Policy Example:** [../policy.yaml](../policy.yaml)
- **Issues:** https://github.com/zhangzhefang-github/agent-governance-gate/issues

## Remember

**"An agent that can do anything is an agent that will do everything."**

Governance exists to:
- Protect the organization from harm
- Protect customers from incorrect actions
- Protect the agent from making mistakes
- Protect the team from blame

When in doubt: ESCALATE.
