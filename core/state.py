from typing import TypedDict, Optional, List, Dict, Any
from core.schemas import AgentEvent


class SupplyChainState(TypedDict, total=False):
    """
    Central LangGraph State Schema tracking data flow across multi-agent nodes.
    Tracks:
      - order_data: Ingested and validated order parameters
      - warehouse_inventory: On-hand inventory, warehouse breakdowns, deficits, reallocation candidates
      - supplier_options: Sourced quotes, lead times, pricing from external suppliers
      - ranked_plans: Synthesized candidate fulfillment options ranked by TOPSIS
      - selected_plan: Highest-ranked fulfillment recommendation
      - explanation: Synthesized business reasoning and trade-off justification
      - status: Current state lifecycle stage
      - approval_status: Human-in-the-loop gate status (PENDING, APPROVED, REJECTED)
      - agent_events: Chronological audit trail of AgentEvents
      - errors: Captured errors, warnings, and fallback telemetry
      - trace_id: Correlation ID for end-to-end tracing
      - metadata: Additional workflow context
    """
    trace_id: str
    order_data: Optional[Dict[str, Any]]
    warehouse_inventory: Optional[Dict[str, Any]]
    supplier_options: Optional[List[Dict[str, Any]]]
    ranked_plans: Optional[List[Dict[str, Any]]]
    selected_plan: Optional[Dict[str, Any]]
    explanation: Optional[str]
    status: str
    approval_status: Optional[str]
    agent_events: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    metadata: Dict[str, Any]
