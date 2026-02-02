# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-XX

### Added
- Initial release of agent-governance-gate
- Core types: Intent, Context, Evidence, Decision, DecisionAction
- Decision pipeline with deterministic precedence (STOP > ESCALATE > RESTRICT > ALLOW)
- Three governance gates: FactVerifiabilityGate, UncertaintyGate, ResponsibilityGate
- YAML-based policy system with condition operators
- Audit trace system with trace_id support
- CLI: `govgate eval` command for evaluating cases
- JSON schemas for type validation
- Customer support policy preset
- Example cases demonstrating same intent, different decisions
- Comprehensive unit and integration tests
