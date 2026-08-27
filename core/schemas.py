from pydantic import BaseModel
from typing import List, Optional

class OrderRequest(BaseModel):
    order_id: str
    customer_id: str
    part_id: str
    requested_qty: int
    max_lead_time_days: int
    priority: str  # "LOW", "MEDIUM", "CRITICAL"

class FulfillmentOption(BaseModel):
    option_id: str
    strategy_name: str
    source: str
    fulfilled_qty: int
    unit_cost: float
    total_cost: float
    lead_time_days: int
    reallocated_from_order: Optional[str] = None
    topsis_score: Optional[float] = None

class StrategyRecommendation(BaseModel):
    order_id: str
    selected_option: FulfillmentOption
    explanation: str
    alternative_options: List[FulfillmentOption]
