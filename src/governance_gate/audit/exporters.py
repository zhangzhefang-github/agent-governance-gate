"""
Exporters for trace data.
"""

from abc import ABC, abstractmethod
from typing import Any
import json


class TraceExporter(ABC):
    """Abstract base class for trace exporters."""

    @abstractmethod
    def export(self, trace_data: dict[str, Any]) -> str:
        """
        Export trace data to a string format.

        Args:
            trace_data: Trace data dictionary

        Returns:
            Exported trace as a string
        """
        pass


class ConsoleExporter(TraceExporter):
    """Exports trace data to human-readable console format."""

    def export(self, trace_data: dict[str, Any]) -> str:
        """Export trace to console-friendly format."""
        lines = []
        lines.append(f"Trace ID: {trace_data['trace_id']}")
        lines.append(f"Event Count: {trace_data['event_count']}")
        lines.append("Events:")

        for event in trace_data.get("events", []):
            lines.append(f"  [{event['timestamp']}] {event['event_type']}: {event['component']}")
            for key, value in event.get("details", {}).items():
                lines.append(f"    {key}: {value}")

        return "\n".join(lines)


class JSONExporter(TraceExporter):
    """Exports trace data to JSON format."""

    def export(self, trace_data: dict[str, Any]) -> str:
        """Export trace to JSON format."""
        return json.dumps(trace_data, indent=2)


class DictExporter(TraceExporter):
    """Exports trace data as a Python dict (returns JSON string for consistency)."""

    def export(self, trace_data: dict[str, Any]) -> str:
        """Export trace as JSON string (dict representation)."""
        return json.dumps(trace_data)
