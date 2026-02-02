"""
CLI for the governance gate system.

Provides commands:
- govgate eval: Evaluate a case and get a decision
- govggate validate: Validate a policy file
"""

import sys
import os
import json
from pathlib import Path
from typing import Any

import click

from governance_gate.core.types import Intent, Context, Evidence, DecisionAction
from governance_gate.core.pipeline import GovernancePipeline
from governance_gate.gates import FactVerifiabilityGate, UncertaintyGate, ResponsibilityGate, SafetyGate
from governance_gate.policy.loader import PolicyLoader
from governance_gate.policy.evaluator import PolicyEvaluator
from governance_gate.policy.schema_validation import PolicyValidationError
from governance_gate.core.errors import GovernanceError, PolicyError


@click.group()
@click.version_option(version="0.1.0")
def cli() -> None:
    """Agent Governance Gate - Framework-agnostic governance for Agent systems."""
    pass


@cli.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--policy",
    "-p",
    type=click.Path(exists=True, path_type=Path),
    help="Path to policy YAML file",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file for decision (JSON)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed trace information",
)
def eval(input_file: Path, policy: Path | None, output: Path | None, verbose: bool) -> None:
    """
    Evaluate a case and produce a governance decision.

    INPUT_FILE: JSON file containing intent, context, and evidence.
    """
    # Load input
    try:
        with open(input_file, "r") as f:
            input_data = json.load(f)
    except json.JSONDecodeError as e:
        click.echo(f"Error: Invalid JSON in input file: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: Failed to read input file: {e}", err=True)
        sys.exit(1)

    # Validate input structure
    if "intent" not in input_data:
        click.echo("Error: Input must contain 'intent' field", err=True)
        sys.exit(1)

    if "context" not in input_data:
        click.echo("Error: Input must contain 'context' field", err=True)
        sys.exit(1)

    if "evidence" not in input_data:
        click.echo("Error: Input must contain 'evidence' field", err=True)
        sys.exit(1)

    # Build Intent, Context, Evidence
    try:
        intent_data = input_data["intent"]
        intent = Intent(
            name=intent_data.get("name", "unknown"),
            confidence=intent_data.get("confidence", 1.0),
            parameters=intent_data.get("parameters", {}),
        )

        context_data = input_data["context"]
        context = Context(
            user_id=context_data.get("user_id"),
            channel=context_data.get("channel"),
            session_id=context_data.get("session_id"),
            metadata=context_data.get("metadata", {}),
        )

        evidence_data = input_data["evidence"]
        evidence = Evidence(
            facts=evidence_data.get("facts", {}),
            rag=evidence_data.get("rag", {}),
            topic=evidence_data.get("topic", {}),
            metadata=evidence_data.get("metadata", {}),
        )
    except Exception as e:
        click.echo(f"Error: Failed to parse input data: {e}", err=True)
        sys.exit(1)

    # Load policy if provided
    policy_evaluator: PolicyEvaluator | None = None
    if policy:
        try:
            loader = PolicyLoader(policy)
            policy_dict = loader.load()
            policy_evaluator = PolicyEvaluator(policy_dict)
        except PolicyError as e:
            click.echo(f"Error: Failed to load policy: {e}", err=True)
            sys.exit(1)

    # Create pipeline
    pipeline = GovernancePipeline(
        gates=[
            SafetyGate(),
            FactVerifiabilityGate(),
            UncertaintyGate(),
            ResponsibilityGate(),
        ]
    )

    # Evaluate
    try:
        decision = pipeline.evaluate(intent, context, evidence, policy_evaluator)
    except GovernanceError as e:
        click.echo(f"Error: Governance evaluation failed: {e}", err=True)
        sys.exit(1)

    # Output decision
    result = {
        "action": decision.action.value,
        "rationale": decision.rationale,
        "trace_id": decision.trace_id,
        "evidence_summary": decision.evidence_summary,
        "gate_contributions": decision.gate_contributions,
        "required_steps": decision.required_steps,
        "final_gate": decision.final_gate,
    }

    if verbose:
        result["verbose"] = {
            "intent": intent_data,
            "context": {k: v for k, v in context_data.items() if k != "metadata"},
            "evidence_keys": list(evidence_data.keys()),
        }

    if output:
        with open(output, "w") as f:
            json.dump(result, f, indent=2)
        click.echo(f"Decision written to {output}")
    else:
        click.echo(json.dumps(result, indent=2))

    # Exit with appropriate code
    sys.exit({
        DecisionAction.ALLOW: 0,
        DecisionAction.RESTRICT: 1,
        DecisionAction.ESCALATE: 2,
        DecisionAction.STOP: 3,
    }[decision.action])


@cli.command()
@click.argument("policy_file", type=click.Path(exists=True, path_type=Path))
def validate(policy_file: Path) -> None:
    """
    Validate a policy YAML file.

    POLICY_FILE: Path to the policy YAML file to validate.
    """
    try:
        loader = PolicyLoader(policy_file)
        policy = loader.load()
        click.echo(f"✓ Policy '{policy.get('name', 'unnamed')}' is valid")
        click.echo(f"  Version: {policy.get('version', 'unknown')}")
        click.echo(f"  Rules: {len(policy.get('rules', []))}")
        click.echo(f"  Gates configured: {list(policy.get('gates', {}).keys())}")
        sys.exit(0)
    except PolicyValidationError as e:
        click.echo(f"✗ Policy validation failed: {e}", err=True)
        sys.exit(1)
    except PolicyError as e:
        click.echo(f"✗ Policy error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--host",
    "-h",
    default="0.0.0.0",
    help="Host to bind to",
)
@click.option(
    "--port",
    "-p",
    default=8000,
    type=int,
    help="Port to bind to",
)
@click.option(
    "--reload",
    is_flag=True,
    help="Enable auto-reload for development",
)
def serve(host: str, port: int, reload: bool) -> None:
    """
    Start the HTTP API server.

    Serves the governance decision API.
    """
    try:
        import uvicorn
    except ImportError:
        click.echo(
            "Error: fastapi/uvicorn not installed.",
            err=True
        )
        click.echo(
            "Install with: pip install -e '.[api]'",
            err=True
        )
        sys.exit(1)

    click.echo(f"Starting Governance Gate API on http://{host}:{port}")
    click.echo(f"API docs: http://{host}:{port}/docs")
    click.echo(f"Policy directory: {os.environ.get('GOVGATE_POLICY_DIR', './policies/presets')}")

    uvicorn.run(
        "governance_gate.api.main:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    cli()
