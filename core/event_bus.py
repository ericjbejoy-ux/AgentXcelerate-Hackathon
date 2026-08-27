import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Callable, Awaitable
from core.schemas import AgentEvent


class EventBus:
    """
    Central Async Event Bus managing agent message dissemination,
    event logging, and real-time frontend streaming.
    """
    def __init__(self):
        self._events: List[AgentEvent] = []
        self._subscribers: List[Callable[[AgentEvent], Awaitable[None]]] = []
        self._lock = asyncio.Lock()

    async def publish(self, event: AgentEvent) -> None:
        """
        Publishes an AgentEvent, records it to history, and notifies subscribers.
        """
        async with self._lock:
            self._events.append(event)
        
        # Dispatch to active subscribers asynchronously
        for subscriber in self._subscribers:
            try:
                res = subscriber(event)
                if asyncio.iscoroutine(res):
                    asyncio.create_task(res)
            except Exception:
                pass  # Subscriber errors shouldn't crash the bus

    def publish_sync(self, event: AgentEvent) -> None:
        """
        Synchronous append helper when outside an active async event loop.
        """
        self._events.append(event)

    def subscribe(self, callback: Callable[[AgentEvent], Awaitable[None]]) -> None:
        """
        Registers an async subscriber callback.
        """
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[AgentEvent], Awaitable[None]]) -> None:
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def get_events_by_trace(self, trace_id: str) -> List[AgentEvent]:
        """
        Returns all events corresponding to a given trace_id.
        """
        return [e for e in self._events if e.trace_id == trace_id]

    def get_all_events(self, limit: int = 200) -> List[AgentEvent]:
        """
        Returns latest logged events.
        """
        return self._events[-limit:]

    def get_all_traces(self) -> List[str]:
        """
        Returns unique trace IDs.
        """
        traces = []
        seen = set()
        for e in reversed(self._events):
            if e.trace_id not in seen:
                seen.add(e.trace_id)
                traces.append(e.trace_id)
        return traces

    def clear(self) -> None:
        """
        Clears event history (useful in testing).
        """
        self._events.clear()


# Global Singleton Event Bus instance
event_bus = EventBus()
