"""
Tests for HTTP API.

Tests the REST endpoints for governance decisions.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))

import pytest

# Skip tests if fastapi is not installed
pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from governance_gate.api.main import app, POLICY_BASE_DIR


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def sample_request():
    """Sample governance request."""
    return {
        "intent": {
            "name": "order_status_query",
            "confidence": 0.95,
            "parameters": {"order_id": "12345"},
        },
        "context": {
            "user_id": "user_123",
            "channel": "web",
            "session_id": "session_456",
        },
        "evidence": {
            "facts": {
                "verifiable": True,
                "verifiable_confidence": 0.9,
                "source": "database",
                "freshness": "fresh",
                "requires_realtime": False,
            },
            "rag": {
                "confidence": 0.85,
                "has_conflicts": False,
            },
            "topic": {
                "has_financial_impact": False,
                "requires_authority": False,
                "is_irreversible": False,
                "is_sensitive": False,
            },
        },
    }


# ============================================================================
# Root Endpoint
# ============================================================================

class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data


# ============================================================================
# Health Endpoint
# ============================================================================

class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health(self, client):
        """Test health endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "policy_base_dir" in data


# ============================================================================
# Decision Endpoint
# ============================================================================

class TestDecisionEndpoint:
    """Tests for decision endpoint."""

    def test_decision_allow(self, client, sample_request):
        """Test decision with ALLOW result."""
        response = client.post("/decision", json=sample_request)

        assert response.status_code == 200
        data = response.json()

        assert "action" in data
        assert "rationale" in data
        assert "trace_id" in data
        assert "timestamp" in data
        assert "gate_decisions" in data

    def test_decision_with_policy(self, client, sample_request):
        """Test decision with policy."""
        sample_request["policy_path"] = "customer_support.yaml"

        response = client.post("/decision", json=sample_request)

        assert response.status_code == 200
        data = response.json()

        assert data["action"] in ["ALLOW", "RESTRICT", "ESCALATE", "STOP"]
        assert data["policy_name"] is not None
        assert data["policy_version"] is not None

    def test_decision_invalid_policy(self, client, sample_request):
        """Test decision with invalid policy path."""
        sample_request["policy_path"] = "nonexistent.yaml"

        response = client.post("/decision", json=sample_request)

        assert response.status_code == 400

    def test_decision_missing_intent(self, client):
        """Test decision with missing intent field."""
        request = {
            "context": {"user_id": "user_123"},
            "evidence": {},
        }

        response = client.post("/decision", json=request)

        assert response.status_code == 422  # Validation error

    def test_decision_restrict_case(self, client):
        """Test decision that results in RESTRICT."""
        request = {
            "intent": {
                "name": "account_balance_query",
                "confidence": 0.9,
            },
            "context": {
                "channel": "web",
            },
            "evidence": {
                "facts": {
                    "verifiable": False,
                    "requires_realtime": True,
                },
                "rag": {
                    "confidence": 0.85,
                },
                "topic": {
                    "has_financial_impact": False,
                },
            },
        }

        response = client.post("/decision", json=request)

        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "RESTRICT"

    def test_decision_escalate_case(self, client):
        """Test decision that results in ESCALATE."""
        request = {
            "intent": {
                "name": "discount_request",
                "confidence": 0.9,
            },
            "context": {
                "channel": "web",
            },
            "evidence": {
                "facts": {
                    "verifiable": True,
                },
                "rag": {
                    "confidence": 0.85,
                },
                "topic": {
                    "has_financial_impact": True,
                },
            },
        }

        response = client.post("/decision", json=request)

        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "ESCALATE"


# ============================================================================
# Policy Validation Endpoint
# ============================================================================

class TestPolicyValidationEndpoint:
    """Tests for policy validation endpoint."""

    def test_validate_policy_valid(self, client):
        """Test validating a valid policy."""
        request = {
            "policy_path": "customer_support.yaml"
        }

        response = client.post("/validate_policy", json=request)

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is True
        assert data["policy_name"] is not None
        assert data["version"] is not None
        assert data["rule_count"] > 0
        assert isinstance(data["gates_configured"], list)

    def test_validate_policy_not_found(self, client):
        """Test validating a nonexistent policy."""
        request = {
            "policy_path": "nonexistent.yaml"
        }

        response = client.post("/validate_policy", json=request)

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is False
        assert len(data["errors"]) > 0

    def test_validate_policy_missing_path(self, client):
        """Test validation with missing policy_path field."""
        response = client.post("/validate_policy", json={})

        assert response.status_code == 422  # Validation error


# ============================================================================
# Error Handling
# ============================================================================

class TestErrorHandling:
    """Tests for error handling."""

    def test_invalid_json(self, client):
        """Test handling of invalid JSON."""
        response = client.post(
            "/decision",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_malformed_request(self, client):
        """Test handling of malformed request."""
        request = {
            "intent": {
                "confidence": 1.5,  # Invalid: > 1.0
            }
        }

        response = client.post("/decision", json=request)

        assert response.status_code == 422
