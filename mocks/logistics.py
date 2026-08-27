"""
Logistics Total Cost Estimator & Carrier Simulator
===================================================
Simulates a dynamic logistics carrier network. Returns dynamic freight quotes
and transit durations using shipment weights, origins, destinations, and speeds.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class FreightQuoteRequest(BaseModel):
    origin: str = Field(..., description="E.g., supplier_a, supplier_b, supplier_c")
    destination: str = Field(..., description="Target delivery zone, e.g., ZONE-EAST, ZONE-WEST")
    sku: str = Field(..., description="Target SKU to calculate weight")
    quantity: int = Field(..., ge=1)
    transit_speed_mode: str = Field("standard", description="standard or express")


class FreightQuoteResponse(BaseModel):
    carrier_name: str
    origin: str
    destination: str
    total_weight_kg: float
    transit_speed_mode: str
    base_rate_usd: float
    weight_markup_usd: float
    speed_factor: float
    freight_cost: float
    carrier_transit_days: float
    supplier_handling_days: float
    total_transit_days: float


# Distance markup matrix from origin supplier to destination zone
_DISTANCE_FACTORS: Dict[str, Dict[str, float]] = {
    "supplier_a": {"ZONE-EAST": 1.0, "ZONE-WEST": 1.5, "ZONE-CENTRAL": 1.2},
    "supplier_b": {"ZONE-EAST": 1.4, "ZONE-WEST": 1.0, "ZONE-CENTRAL": 1.1},
    "supplier_c": {"ZONE-EAST": 2.2, "ZONE-WEST": 2.5, "ZONE-CENTRAL": 2.0},  # Alt region is far
}


def calculate_freight_quote(
    origin: str,
    destination: str,
    weight_kg: float,
    quantity: int,
    speed_mode: str,
    supplier_handling_days: float,
    base_freight_rate: float,
    speed_factor_val: float,
) -> FreightQuoteResponse:
    """
    Calculate dynamic freight charges using:
        Total Weight = weight_kg * quantity
        Freight Cost = (Base Freight + Weight Markup) * e^(Speed Factor) * Distance Factor
    """
    total_weight = round(weight_kg * quantity, 2)
    
    # Base weight surcharge
    weight_markup = round(total_weight * 0.15, 2)  # $0.15 per kg
    
    # Speed Mode modifiers
    if speed_mode.lower() == "express":
        applied_speed_factor = speed_factor_val * 1.5
        carrier_days = 1.5  # Express shipping is fast
    else:
        applied_speed_factor = speed_factor_val
        carrier_days = 4.0  # Standard shipping is slower

    # Distance factor lookup
    zone_rates = _DISTANCE_FACTORS.get(origin.lower(), {})
    distance_mult = zone_rates.get(destination.upper(), 1.2)
    
    # Calculate freight cost: Base * e^Speed
    raw_freight = (base_freight_rate + weight_markup) * math.exp(applied_speed_factor)
    freight_cost = round(raw_freight * distance_mult, 2)
    
    total_transit_days = supplier_handling_days + carrier_days

    return FreightQuoteResponse(
        carrier_name="Nexus Logistics Carrier Network",
        origin=origin,
        destination=destination,
        total_weight_kg=total_weight,
        transit_speed_mode=speed_mode.upper(),
        base_rate_usd=base_freight_rate,
        weight_markup_usd=weight_markup,
        speed_factor=round(applied_speed_factor, 2),
        freight_cost=freight_cost,
        carrier_transit_days=carrier_days,
        supplier_handling_days=supplier_handling_days,
        total_transit_days=total_transit_days
    )
