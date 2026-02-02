"""
FastAPI HTTP API for governance decisions.

Provides framework-agnostic REST endpoints for evaluating governance decisions.
"""

import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from governance_gate.core.types import Intent, Context, Evidence, DecisionAction
from governance_gate.core.pipeline import GovernancePipeline
from governance_gate.gates import FactVerifiabilityGate, UncertaintyGate, ResponsibilityGate, SafetyGate
from governance_gate.policy.loader import PolicyLoader
from governance_gate.policy.evaluator import PolicyEvaluator
from governance_gate.policy.schema_validation import PolicyValidationError
from governance_gate.core.errors import GovernanceError, PolicyError
from governance_gate.api.models import (
    GovernanceRequest,
    DecisionResponse,
    PolicyValidationRequest,
    PolicyValidationResponse,
    HealthResponse,
    GateDecisionResponse,
)

# Configuration
POLICY_BASE_DIR = os.environ.get("GOVGATE_POLICY_DIR", "./policies/presets")
API_VERSION = "0.1.0"

# Create FastAPI app
app = FastAPI(
    title="Governance Gate API",
    description="Framework-agnostic governance decisions for Agent systems",
    version=API_VERSION,
)


# ============================================================================
# Dependencies
# ============================================================================

def get_policy_loader(policy_path: str) -> PolicyLoader:
    """Get a policy loader for the given path."""
    full_path = Path(POLICY_BASE_DIR) / policy_path
    return PolicyLoader(full_path)


def create_pipeline() -> GovernancePipeline:
    """Create a default governance pipeline."""
    return GovernancePipeline(
        gates=[
            SafetyGate(),
            FactVerifiabilityGate(),
            UncertaintyGate(),
            ResponsibilityGate(),
        ]
    )


# ============================================================================
# Endpoints
# ============================================================================

@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Governance Gate API",
        "version": API_VERSION,
        "endpoints": {
            "health": "GET /health",
            "decision": "POST /decision",
            "validate_policy": "POST /validate_policy",
        },
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=API_VERSION,
        policy_base_dir=str(Path(POLICY_BASE_DIR).resolve()),
    )


@app.post("/decision", response_model=DecisionResponse, status_code=status.HTTP_200_OK)
async def evaluate_decision(request: GovernanceRequest):
    """
    Evaluate a governance decision.

    Args:
        request: Governance request with intent, context, and evidence

    Returns:
        Decision with action, rationale, and trace information
    """
    try:
        # Load policy if specified
        policy_evaluator: Optional[PolicyEvaluator] = None
        policy_version = None
        policy_name = None

        if request.policy_path:
            try:
                loader = get_policy_loader(request.policy_path)
                policy_dict = loader.load()
                policy_evaluator = PolicyEvaluator(policy_dict)
                policy_version = policy_dict.get("version")
                policy_name = policy_dict.get("name")
            except (PolicyError, PolicyValidationError, FileNotFoundError) as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Policy error: {e}"
                )

        # Build Intent
        intent = Intent(
            name=request.intent.name,
            confidence=request.intent.confidence,
            parameters=request.intent.parameters,
        )

        # Build Context
        context = Context(
            user_id=request.context.user_id,
            channel=request.context.channel,
            session_id=request.context.session_id,
            metadata=request.context.metadata,
        )

        # Build Evidence
        evidence = Evidence(
            facts=request.evidence.facts,
            rag=request.evidence.rag,
            topic=request.evidence.topic,
            metadata=request.evidence.metadata,
        )

        # Create pipeline and evaluate
        pipeline = create_pipeline()
        decision = pipeline.evaluate(intent, context, evidence, policy_evaluator)

        # Convert gate_decisions to response format
        gate_decisions = {}
        for gate_name, gate_decision in decision.gate_decisions.items():
            gate_decisions[gate_name] = GateDecisionResponse(
                gate_name=gate_decision.gate_name,
                suggested_action=gate_decision.suggested_action,
                rationale=gate_decision.rationale,
                config_used=gate_decision.config_used,
                input_summary=gate_decision.input_summary,
            )

        # Use the decision_code from the pipeline (already generated)
        decision_code = decision.decision_code or f"GOVERNANCE_{decision.action.value}"

        return DecisionResponse(
            action=decision.action.value,
            rationale=decision.rationale,
            trace_id=decision.trace_id,
            policy_version=decision.policy_version,
            policy_name=decision.policy_name,
            decision_code=decision_code,
            final_gate=decision.final_gate,
            gate_decisions=gate_decisions,
            evidence_summary=decision.evidence_summary,
            required_steps=decision.required_steps,
            timestamp=decision.timestamp,
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {e}"
        )
    except HTTPException:
        # Re-raise HTTPException as-is
        raise
    except GovernanceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Governance error: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {e}"
        )


@app.post("/validate_policy", response_model=PolicyValidationResponse)
async def validate_policy(request: PolicyValidationRequest):
    """
    Validate a policy file.

    Args:
        request: Policy validation request

    Returns:
        Validation result with policy info and any errors
    """
    try:
        full_path = Path(POLICY_BASE_DIR) / request.policy_path

        if not full_path.exists():
            return PolicyValidationResponse(
                valid=False,
                errors=[f"Policy file not found: {full_path}"]
            )

        loader = PolicyLoader(full_path)
        policy = loader.load()

        return PolicyValidationResponse(
            valid=True,
            policy_name=policy.get("name"),
            version=policy.get("version"),
            rule_count=len(policy.get("rules", [])),
            gates_configured=list(policy.get("gates", {}).keys()),
        )

    except PolicyValidationError as e:
        return PolicyValidationResponse(
            valid=False,
            errors=[str(e)]
        )
    except PolicyError as e:
        return PolicyValidationResponse(
            valid=False,
            errors=[str(e)]
        )
    except Exception as e:
        return PolicyValidationResponse(
            valid=False,
            errors=[f"Unexpected error: {e}"]
        )


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


# ============================================================================
# Startup Event
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    import logging
    logger = logging.getLogger("governance_gate.api")
    logger.info(f"Governance Gate API v{API_VERSION} starting")
    logger.info(f"Policy base directory: {Path(POLICY_BASE_DIR).resolve()}")


# ============================================================================
# Run Directly (for development)
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "governance_gate.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
