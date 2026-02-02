"""
Request and response models for the HTTP API.
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class IntentRequest(BaseModel):
    """Intent data from request."""

    name: str = Field(..., description="Intent identifier")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ContextRequest(BaseModel):
    """Context data from request."""

    user_id: Optional[str] = None
    channel: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvidenceRequest(BaseModel):
    """Evidence data from request."""

    facts: Dict[str, Any] = Field(default_factory=dict)
    rag: Dict[str, Any] = Field(default_factory=dict)
    topic: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GovernanceRequest(BaseModel):
    """Request body for governance decision."""

    intent: IntentRequest
    context: ContextRequest = Field(default_factory=ContextRequest)
    evidence: EvidenceRequest = Field(default_factory=EvidenceRequest)
    policy_path: Optional[str] = Field(
        None, description="Path to policy YAML file (relative to POLICY_BASE_DIR)"
    )


class GateDecisionResponse(BaseModel):
    """Decision from a single gate."""

    gate_name: str
    suggested_action: Optional[str]
    rationale: str
    config_used: Optional[Dict[str, Any]] = None
    input_summary: Optional[Dict[str, Any]] = None


class DecisionResponse(BaseModel):
    """Response body for governance decision."""

    action: str
    rationale: str
    trace_id: str
    policy_version: Optional[str] = None
    policy_name: Optional[str] = None
    decision_code: Optional[str] = None
    final_gate: Optional[str] = None  # Name of gate that determined final action (None for ALLOW)
    gate_decisions: Dict[str,GateDecisionResponse] = Field(default_factory=dict)
    evidence_summary: Dict[str, Any] = Field(default_factory=dict)
    required_steps: List[str] = Field(default_factory=list)
    timestamp: str


class PolicyValidationRequest(BaseModel):
    """Request body for policy validation."""

    policy_path: str = Field(..., description="Path to policy YAML file")


class PolicyValidationResponse(BaseModel):
    """Response body for policy validation."""

    valid: bool
    policy_name: Optional[str] = None
    version: Optional[str] = None
    rule_count: int = 0
    gates_configured: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    policy_base_dir: str
