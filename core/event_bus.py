"""
Event Bus for Agent Communication
================================
Lightweight audit log for agent-to-agent communication with trace_id tracking.
"""
from __future__ import annotations

import logging
import uuid
import threading
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from core.schemas import AgentEvent

logger = logging.getLogger("event_bus")


class EventBus:
    """
    Audit-log event bus for agent communication.

    Stores events with trace_id for distributed tracing.
    Subscribers are called synchronously on publish.
    """

    def __init__(self, max_history: int = 1000):
        self._subscribers: List = []
        self._message_history: List[AgentEvent] = []
        self._max_history = max_history
        self._lock = threading.Lock()
        self._agent_registry: Dict[str, Dict[str, Any]] = {}

    def register_agent(self, agent_id: str, agent_type: str, capabilities: List[str] = None) -> None:
        self._agent_registry[agent_id] = {
            "agent_type": agent_type,
            "capabilities": capabilities or [],
            "registered_at": datetime.now(timezone.utc).isoformat(),
        }

    def subscribe(self, agent_id: str, callback) -> None:
        entry = {"agent_id": agent_id, "callback": callback}
        if entry not in self._subscribers:
            self._subscribers.append(entry)

    def unsubscribe(self, agent_id: str) -> None:
        self._subscribers = [s for s in self._subscribers if s["agent_id"] != agent_id]

    def publish_sync(self, event: AgentEvent) -> None:
        with self._lock:
            self._message_history.append(event)
            if len(self._message_history) > self._max_history:
                self._message_history = self._message_history[-self._max_history:]

        for subscriber in self._subscribers:
            try:
                subscriber["callback"](event)
            except Exception as e:
                logger.warning("Subscriber %s failed: %s", subscriber["agent_id"], e)

    async def publish(self, event: AgentEvent) -> None:
        self.publish_sync(event)

    def get_events_by_trace(self, trace_id: str) -> List[AgentEvent]:
        return [e for e in self._message_history if e.trace_id == trace_id]

    def get_all_events(self, limit: int = 200) -> List[AgentEvent]:
        return self._message_history[-limit:]

    def get_all_traces(self) -> List[str]:
        traces = []
        seen = set()
        for e in reversed(self._message_history):
            if e.trace_id not in seen:
                seen.add(e.trace_id)
                traces.append(e.trace_id)
        return traces

    def clear(self) -> None:
        self._message_history.clear()


# Global singleton
_bus_instance: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    global _bus_instance
    if _bus_instance is None:
        _bus_instance = EventBus()
    return _bus_instance


event_bus = get_event_bus()


def create_event(
    sender_agent: str,
    event_type: str,
    data: Dict[str, Any],
    recipient_agent: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> AgentEvent:
    """Helper to create a properly formatted AgentEvent."""
    return AgentEvent(
        trace_id=trace_id or str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
        sender_agent=sender_agent,
        recipient_agent=recipient_agent,
        event_type=event_type,
        data=data,
    )
