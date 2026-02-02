# Failure Mode Configuration

## Overview

The governance gate API supports two failure modes to handle errors gracefully:

- **fail_closed** (default, recommended for production): Returns ESCALATE on errors
- **fail_open** (testing only): Returns RESTRICT with warning on errors

## Configuration

Set via environment variable:

```bash
# Default (recommended for production)
export GOVGATE_FAILURE_MODE=fail_closed

# For testing/development only
export GOVGATE_FAILURE_MODE=fail_open
```

## Behavior

### fail_closed (Default)

**When governance gate fails:**
- Policy load error → ESCALATE
- Pipeline evaluation error → ESCALATE
- System error → ESCALATE

**Rationale:** Conservative - human review required when governance is unavailable

**Use case:** Production systems where avoiding unauthorized actions is critical

### fail_open (Testing Only)

**When governance gate fails:**
- Policy load error → RESTRICT with warning
- Pipeline evaluation error → RESTRICT with warning
- System error → RESTRICT with warning

**Rationale:** Less conservative - allow limited responses when governance is unavailable

**Use case:** Development, testing, or demo environments

**⚠️ Warning:** Never use fail_open in production without careful consideration!

## Example Scenarios

### Scenario 1: Policy File Missing

**fail_closed:**
```json
{
  "action": "ESCALATE",
  "rationale": "Governance unavailable (fail-closed mode): Policy file not found",
  "required_steps": ["Manual review required due to governance system failure"]
}
```

**fail_open:**
```json
{
  "action": "RESTRICT",
  "rationale": "Governance unavailable (fail-open mode): Policy file not found. Response limited.",
  "required_steps": ["System unavailable - showing limited response"]
}
```

### Scenario 2: Pipeline Exception

**fail_closed:**
```json
{
  "action": "ESCALATE",
  "rationale": "System error (fail-closed mode): Division by zero in gate",
  "required_steps": ["Manual review required due to system failure"]
}
```

**fail_open:**
```json
{
  "action": "RESTRICT",
  "rationale": "System error (fail-open mode): Division by zero. Showing limited response.",
  "required_steps": ["System unavailable - showing limited response"]
}
```

## Best Practices

### Production

✅ **Always use fail_closed in production**

```bash
export GOVGATE_FAILURE_MODE=fail_closed
govgate serve --port 8000
```

**Why:**
- Prevents unauthorized actions when governance is unavailable
- Ensures human oversight in error scenarios
- Aligns with "responsibility engineering" principles

### Development

Option 1: Use fail_closed (still recommended)
```bash
export GOVGATE_FAILURE_MODE=fail_closed
```

Option 2: Use fail_open (only for testing)
```bash
export GOVGATE_FAILURE_MODE=fail_open
govgate serve --port 8000
```

**Why:**
- fail_open allows you to continue working when testing
- Reduces friction during development
- Still logs warnings for visibility

### Monitoring

**Alert on governance failures:**

```python
# Log warning when fail_open is used
if config.failure_mode == "fail_open":
    logger.warning(
        "Running in fail_open mode - not recommended for production",
        extra={"mode": "fail_open"}
    )
```

**Track failure rate:**

```promql
# Governance errors per minute
rate(governance_errors_total[1m])

# Percentage of requests failing
rate(governance_errors_total[5m]) / rate(governance_decisions_total[5m])
```

## Testing Failure Modes

### Test fail_closed

```bash
# Set mode
export GOVGATE_FAILURE_MODE=fail_closed

# Start API
govgate serve --port 8000

# Test with invalid policy (should return ESCALATE)
curl -X POST http://localhost:8000/decision \
  -H "Content-Type: application/json" \
  -d '{
    "intent": {"name": "test", "confidence": 0.9},
    "context": {},
    "evidence": {},
    "policy_path": "nonexistent.yaml"
  }'

# Expected: ESCALATE with "Manual review required"
```

### Test fail_open

```bash
# Set mode
export GOVGATE_FAILURE_MODE=fail_open

# Start API
govgate serve --port 8000

# Test with invalid policy (should return RESTRICT)
curl -X POST http://localhost:8000/decision \
  -H "Content-Type: application/json" \
  -d '{
    "intent": {"name": "test", "confidence": 0.9},
    "context": {},
    "evidence": {},
    "policy_path": "nonexistent.yaml"
  }'

# Expected: RESTRICT with "Response limited"
```

## Implementation Details

### API Layer Only

The failure mode is implemented **only at the API layer** (`src/governance_gate/api/`).

**Core pipeline is unchanged:**
- `core/pipeline.py` - No changes
- `core/decision.py` - No changes
- `gates/` - No changes

This keeps the core logic clean and focused.

### Where It's Used

Failure mode applies to:
1. Policy load errors (`PolicyError`, `PolicyValidationError`, `FileNotFoundError`)
2. Pipeline evaluation errors (`GovernanceError`)
3. Unexpected system errors (`Exception`)

**Does NOT apply to:**
- Validation errors (422) - client error, always raise HTTPException
- Explicit HTTPException - re-raised as-is

### Code Location

```python
# src/governance_gate/api/config.py
@dataclass
class APIConfig:
    failure_mode: Literal["fail_closed", "fail_open"] = "fail_closed"

# src/governance_gate/api/main.py
except (GovernanceError, PolicyError) as e:
    if config.failure_mode == "fail_closed":
        return ESCALATE
    else:
        return RESTRICT
```

## Troubleshooting

### Problem: API returns ESCALATE unexpectedly

**Diagnosis:**
```bash
# Check current mode
curl http://localhost:8000/health | jq .failure_mode

# Check logs for errors
govgate logs | grep "Governance unavailable"
```

**Possible causes:**
1. Policy file path is incorrect
2. Policy YAML has syntax errors
3. Gate configuration is invalid

### Problem: Want to test error handling

**Solution:**
1. Create an invalid policy file
2. Test with `GOVGATE_FAILURE_MODE=fail_closed`
3. Verify ESCALATE response
4. Switch to `fail_open` and verify RESTRICT response

### Problem: Need different behavior

**The current implementation only supports ESCALATE/RESTRICT on errors.**

If you need different behavior (e.g., ALLOW, STOP), you can:

1. Modify `src/governance_gate/api/main.py` exception handlers
2. Add custom logic based on error type
3. Submit a PR with your use case

## Migration Guide

### From v0.1.0 (no failure mode)

**Before:** Errors returned HTTP 500

**After (v0.1.1+):**
- Default (fail_closed): Returns ESCALATE
- Optional (fail_open): Returns RESTRICT

**Action required:**
- None - backward compatible if you want ESCALATE on errors
- Set `GOVGATE_FAILURE_MODE=fail_open` if you want RESTRICT instead

### Checklist for Production

- [ ] Set `GOVGATE_FAILURE_MODE=fail_closed` (default)
- [ ] Test with invalid policy to verify ESCALATE behavior
- [ ] Add alerting for governance failures
- [ ] Document escalation procedures for operations team
- [ ] Run load test to verify failure handling under load
- [ ] Review logs for governance errors and adjust configuration

## Security Considerations

### fail_closed

**Security:** ✅ Most secure

**Behavior:** Always requires human review when governance fails

**Risk:** Low - humans are in the loop

### fail_open

**Security:** ⚠️  Less secure

**Behavior:** Allows limited responses without governance

**Risk:** Higher - could allow unintended actions

**Never use fail_open when:**
- Handling financial transactions
- Modifying user data
- Executing sensitive operations
- In regulated environments (finance, healthcare, etc.)
