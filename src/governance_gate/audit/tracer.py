"""
Audit tracer for recording decision trace information.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from collections import OrderedDict


@dataclass
class TraceEvent:
    """
    Represents a single trace event.

    Attributes:
        timestamp: When the event occurred
        event_type: Type of event (e.g., "gate_evaluated", "decision_made")
        component: Component that generated the event (e.g., gate name)
        details: Additional event details
    """

    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_type: str = ""
    component: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "component": self.component,
            "details": self.details,
        }


class AuditTracer:
    """
    Records trace events for governance decisions.

    The tracer maintains an ordered list of events that occurred during
    pipeline evaluation, enabling full auditability of decisions.
    """

    def __init__(self, trace_id: str | None = None) -> None:
        """
        Initialize the tracer.

        Args:
            trace_id: Optional trace ID (generated if not provided)
        """
        import uuid

        self.trace_id = trace_id or str(uuid.uuid4())
        self.events: list[TraceEvent] = []

    def record_event(
        self,
        event_type: str,
        component: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Record a trace event.

        Args:
            event_type: Type of event
            component: Component name
            details: Optional event details
        """
        event = TraceEvent(
            event_type=event_type,
            component=component,
            details=details or {},
        )
        self.events.append(event)

    def record_gate_evaluation(
        self,
        gate_name: str,
        action: str | None,
        rationale: str,
        duration_ms: float | None = None,
    ) -> None:
        """
        Record a gate evaluation event.

        Args:
            gate_name: Name of the gate
            action: Action returned by the gate (if any)
            rationale: Rationale from the gate
            duration_ms: Evaluation duration in milliseconds
        """
        self.record_event(
            event_type="gate_evaluated",
            component=gate_name,
            details={
                "action": action,
                "rationale": rationale,
                "duration_ms": duration_ms,
            },
        )

    def record_decision(
        self,
        final_action: str,
        rationale: str,
        gate_contributions: dict[str, str],
    ) -> None:
        """
        Record the final decision event.

        Args:
            final_action: The final decision action
            rationale: The final rationale
            gate_contributions: Contributions from each gate
        """
        self.record_event(
            event_type="decision_made",
            component="pipeline",
            details={
                "action": final_action,
                "rationale": rationale,
                "gate_contributions": gate_contributions,
            },
        )

    def get_events(self) -> list[dict[str, Any]]:
        """Get all events as dictionaries."""
        return [event.to_dict() for event in self.events]

    def get_trace_summary(self) -> dict[str, Any]:
        """
        Get a summary of the trace.

        Returns:
            Dictionary with trace_id, event_count, and events
        """
        return {
            "trace_id": self.trace_id,
            "event_count": len(self.events),
            "events": self.get_events(),
        }

    def clear(self) -> None:
        """Clear all events from the tracer."""
        self.events.clear()
