"""
Demand Agent
============
Processes an incoming order dict and produces fulfillment candidates
scored by cost, lead time, reliability, and distance for TOPSIS ranking.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from mocks.inventory_db import SKU_CATALOG, WAREHOUSE_STOCK, get_stock
from mocks.suppliers import SupplierID, MockSupplierAPI


# Priority → weight profiles (higher priority = heavier lead-time weight)
_PRIORITY_WEIGHTS = {
    "LOW":      {"cost": 0.40, "lead_time": 0.20, "reliability": 0.25, "distance": 0.15},
    "MEDIUM":   {"cost": 0.25, "lead_time": 0.35, "reliability": 0.30, "distance": 0.10},
    "HIGH":     {"cost": 0.15, "lead_time": 0.50, "reliability": 0.25, "distance": 0.10},
    "CRITICAL": {"cost": 0.10, "lead_time": 0.60, "reliability": 0.20, "distance": 0.10},
}

# Distance proxies for supplier zones (km)
_SUPPLIER_DISTANCES = {
    "supplier_a": 120,   # Primary — closest
    "supplier_b": 450,   # Express — remote
    "supplier_c": 800,   # Alt region — farthest
}

# Reliability proxies per supplier
_SUPPLIER_RELIABILITY = {
    "supplier_a": 0.95,
    "supplier_b": 0.88,
    "supplier_c": 0.82,
}


def _resolve_weights(priority: str) -> Dict[str, float]:
    return _PRIORITY_WEIGHTS.get(priority.upper(), _PRIORITY_WEIGHTS["MEDIUM"])


def _build_candidates_from_warehouse(part_id: str, requested_qty: int) -> List[Dict[str, Any]]:
    """Build candidates from internal warehouse stock."""
    candidates = []
    for sku_key, stock in WAREHOUSE_STOCK.items():
        sku_rec = SKU_CATALOG.get(sku_key)
        if sku_rec is None:
            continue
        available = stock.available_qty
        # Accept if it has any stock at all, or matches the requested part loosely
        candidates.append({
            "candidate_id": f"WH-{sku_key[-3:]}",
            "warehouse_id": stock.warehouse_loc,
            "warehouse_loc": stock.warehouse_loc,
            "source": "Internal Warehouse",
            "sku": sku_key,
            "description": sku_rec.description,
            "category": sku_rec.category,
            "available_stock": available,
            "current_stock": stock.on_hand_qty,
            "allocated_stock": stock.reserved_qty,
            "remaining_stock": available,
            "unit_cost": sku_rec.base_unit_price,
            "total_cost": round(sku_rec.base_unit_price * requested_qty, 2),
            "lead_time_days": 2,           # internal = fast
            "reliability_score": 0.97,     # own warehouse = most reliable
            "distance": 50,                # local
            "can_fulfill": available >= requested_qty,
            "fulfillment_type": "Direct Warehouse Stock",
        })
    return candidates


async def _build_candidates_from_suppliers(part_id: str, requested_qty: int) -> List[Dict[str, Any]]:
    """Query all mock supplier APIs concurrently and build candidate rows."""
    candidates = []
    tasks = {}
    for sid in SupplierID:
        api = MockSupplierAPI(sid)
        tasks[sid.value] = api
    
    # Gather quotes for every SKU from every supplier
    for sid_val, api in tasks.items():
        catalog = await api.get_catalog()
        for item in catalog.items:
            candidates.append({
                "candidate_id": f"{sid_val.upper()[:3]}-{item.sku[-3:]}",
                "warehouse_id": f"{api.supplier_name}",
                "warehouse_loc": api.supplier_name,
                "source": api.supplier_name,
                "sku": item.sku,
                "description": item.description,
                "category": "Supplier Stock",
                "available_stock": item.available_qty,
                "current_stock": item.available_qty,
                "allocated_stock": 0,
                "remaining_stock": item.available_qty,
                "unit_cost": item.unit_price,
                "total_cost": round(item.unit_price * requested_qty, 2),
                "lead_time_days": api.lead_time_days,
                "reliability_score": _SUPPLIER_RELIABILITY.get(sid_val, 0.85),
                "distance": _SUPPLIER_DISTANCES.get(sid_val, 500),
                "can_fulfill": item.available_qty >= requested_qty,
                "fulfillment_type": "Supplier Order",
            })
    return candidates


def process_demand_layer(order_dict: dict) -> dict:
    """
    Main entry point called by main.py.
    Returns: {"candidates": [...], "weights": {...}}
    """
    part_id = order_dict.get("part_id", "")
    requested_qty = int(order_dict.get("requested_qty", 1))
    priority = order_dict.get("priority", "MEDIUM").upper()

    weights = _resolve_weights(priority)

    # Build warehouse candidates (sync)
    wh_candidates = _build_candidates_from_warehouse(part_id, requested_qty)

    # Build supplier candidates (async, run in event loop)
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, _build_candidates_from_suppliers(part_id, requested_qty))
                sup_candidates = future.result()
        else:
            sup_candidates = loop.run_until_complete(_build_candidates_from_suppliers(part_id, requested_qty))
    except Exception:
        sup_candidates = []

    all_candidates = wh_candidates + sup_candidates

    return {
        "candidates": all_candidates,
        "weights": weights,
        "order_id": order_dict.get("order_id", "ORD-UNKNOWN"),
        "part_id": part_id,
        "requested_qty": requested_qty,
        "priority": priority,
    }
