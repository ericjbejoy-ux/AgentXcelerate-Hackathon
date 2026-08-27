"""
Logistics Total Cost Estimator & Constraint Verifier
=====================================================
Calculates total landed cost and filters supplier paths by lead-time constraints.

Landed Cost formula:
    Landed_Cost = (Unit_Price × Q) + Freight_Base_Rate × e^(Speed_Factor)
"""

from __future__ import annotations

import math
from typing import List, Optional

from pydantic import BaseModel, Field

from mocks.suppliers import SupplierQuote


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class LandedCostBreakdown(BaseModel):
    """Detailed cost breakdown for a supplier quote."""
    supplier_id: str
    supplier_name: str
    sku: str
    quantity: int
    unit_price: float
    item_subtotal: float = Field(description="Unit Price × Quantity")
    freight_base_rate: float
    speed_factor: float
    freight_cost: float = Field(description="Freight Base Rate × e^(Speed Factor)")
    total_landed_cost: float = Field(description="Item subtotal + freight cost")
    lead_time_days: float
    in_stock: bool


class FilteredSupplierResult(BaseModel):
    """Result of constraint verification — viable supplier paths."""
    viable: List[LandedCostBreakdown] = Field(
        default_factory=list,
        description="Suppliers that meet the lead-time constraint, sorted by cost",
    )
    rejected: List[LandedCostBreakdown] = Field(
        default_factory=list,
        description="Suppliers that exceed the lead-time constraint",
    )
    max_lead_time_days: float
    cheapest: Optional[LandedCostBreakdown] = Field(
        default=None,
        description="Lowest cost viable option (None if none are viable)",
    )
    fastest: Optional[LandedCostBreakdown] = Field(
        default=None,
        description="Fastest viable option (None if none are viable)",
    )


# ---------------------------------------------------------------------------
# Cost Estimator
# ---------------------------------------------------------------------------

def calculate_landed_cost(
    unit_price: float,
    quantity: int,
    freight_base_rate: float,
    speed_factor: float,
) -> tuple[float, float, float]:
    """
    Compute landed cost using the formula:
        Landed Cost = (Unit Price × Q) + Freight Base Rate × e^(Speed Factor)

    Returns:
        (item_subtotal, freight_cost, total_landed_cost)
    """
    item_subtotal = unit_price * quantity
    freight_cost = freight_base_rate * math.exp(speed_factor)
    total = item_subtotal + freight_cost
    return (
        round(item_subtotal, 2),
        round(freight_cost, 2),
        round(total, 2),
    )


def build_cost_breakdown(
    quote: SupplierQuote,
    quantity: int,
) -> LandedCostBreakdown:
    """Build a full cost breakdown from a supplier quote and desired quantity."""
    item_sub, freight, total = calculate_landed_cost(
        unit_price=quote.unit_price,
        quantity=quantity,
        freight_base_rate=quote.freight_base_rate,
        speed_factor=quote.speed_factor,
    )
    return LandedCostBreakdown(
        supplier_id=quote.supplier_id,
        supplier_name=quote.supplier_name,
        sku=quote.sku,
        quantity=quantity,
        unit_price=quote.unit_price,
        item_subtotal=item_sub,
        freight_base_rate=quote.freight_base_rate,
        speed_factor=quote.speed_factor,
        freight_cost=freight,
        total_landed_cost=total,
        lead_time_days=quote.lead_time_days,
        in_stock=quote.in_stock,
    )


# ---------------------------------------------------------------------------
# Constraint Verifier
# ---------------------------------------------------------------------------

def filter_by_lead_time(
    breakdowns: List[LandedCostBreakdown],
    max_lead_time_days: float,
) -> FilteredSupplierResult:
    """
    Partition supplier cost breakdowns into viable / rejected based on a
    customer's maximum lead-time threshold.

    Viable results are sorted ascending by ``total_landed_cost``.
    """
    viable: List[LandedCostBreakdown] = []
    rejected: List[LandedCostBreakdown] = []

    for bd in breakdowns:
        if bd.lead_time_days <= max_lead_time_days:
            viable.append(bd)
        else:
            rejected.append(bd)

    viable.sort(key=lambda b: b.total_landed_cost)

    cheapest = viable[0] if viable else None
    fastest = min(viable, key=lambda b: b.lead_time_days) if viable else None

    return FilteredSupplierResult(
        viable=viable,
        rejected=rejected,
        max_lead_time_days=max_lead_time_days,
        cheapest=cheapest,
        fastest=fastest,
    )


# ---------------------------------------------------------------------------
# High-level convenience
# ---------------------------------------------------------------------------

async def evaluate_suppliers(
    sku: str,
    quantity: int,
    max_lead_time_days: float,
) -> FilteredSupplierResult:
    """
    End-to-end helper: query all suppliers → compute landed costs → filter.

    This is the primary entry-point other agents/modules should call.
    """
    from mocks.suppliers import query_all_suppliers

    quotes = await query_all_suppliers(sku, quantity)

    breakdowns = [build_cost_breakdown(q, quantity) for q in quotes]

    return filter_by_lead_time(breakdowns, max_lead_time_days)
