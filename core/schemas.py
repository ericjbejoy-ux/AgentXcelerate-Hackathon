from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import uuid


class OrderRequest(BaseModel):
    order_id: Optional[str] = None
    customer_id: str
    part_id: str
    requested_qty: int
    max_lead_time_days: int
    priority: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    raw_text: Optional[str] = None
    notes: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    user_location_city: Optional[str] = None


class UnstructuredOrderRequest(BaseModel):
    raw_text: str
    customer_id: Optional[str] = None
    override_priority: Optional[str] = None


class ApprovalRequest(BaseModel):
    order_id: str
    trace_id: Optional[str] = None
    action: str  # "APPROVE" or "REJECT"
    notes: Optional[str] = ""


class AgentEvent(BaseModel):
    trace_id: str
    sender_agent: str
    recipient_agent: Optional[str] = None
    event_type: str
    data: Dict[str, Any] = {}
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    event_id: str = Field(default_factory=lambda: f"evt-{uuid.uuid4().hex[:8]}")


class FulfillmentOption(BaseModel):
    option_id: str
    strategy_name: str
    source: str
    fulfilled_qty: int
    unit_cost: float
    total_cost: float
    lead_time_days: int
    reliability_score: Optional[float] = 0.9
    warehouse_id: Optional[str] = None
    reallocated_from_order: Optional[str] = None
    topsis_score: Optional[float] = None


class StrategyRecommendation(BaseModel):
    order_id: str
    selected_option: FulfillmentOption
    explanation: str
    alternative_options: List[FulfillmentOption]
