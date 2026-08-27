"""
Inventory Agent
===============
Provides read access to the centralized SKU catalog and warehouse stock levels.
Used by API endpoints to serve frontend inventory dashboard data.
"""

from __future__ import annotations

from typing import Any, Dict, List

from mocks.inventory_db import SKU_CATALOG, WAREHOUSE_STOCK


def get_full_inventory() -> List[Dict[str, Any]]:
    """Return all SKUs with their warehouse stock as a flat list of dicts."""
    result = []
    for sku_key, sku_rec in SKU_CATALOG.items():
        stock = WAREHOUSE_STOCK.get(sku_key)
        entry: Dict[str, Any] = {
            "sku": sku_key,
            "description": sku_rec.description,
            "category": sku_rec.category,
            "base_unit_price": sku_rec.base_unit_price,
            "unit_of_measure": sku_rec.unit_of_measure,
            "weight_kg": sku_rec.weight_kg,
            "is_critical": sku_rec.critical,
        }
        if stock:
            entry.update({
                "on_hand_qty": stock.on_hand_qty,
                "reserved_qty": stock.reserved_qty,
                "available_qty": stock.available_qty,
                "reorder_point": stock.reorder_point,
                "max_capacity": stock.max_capacity,
                "warehouse_loc": stock.warehouse_loc,
                "needs_reorder": stock.needs_reorder,
                "stock_pct": round((stock.available_qty / stock.max_capacity) * 100, 1) if stock.max_capacity > 0 else 0,
            })
        else:
            entry.update({
                "on_hand_qty": 0,
                "reserved_qty": 0,
                "available_qty": 0,
                "reorder_point": 0,
                "max_capacity": 0,
                "warehouse_loc": "N/A",
                "needs_reorder": True,
                "stock_pct": 0,
            })
        result.append(entry)
    return result


def get_low_stock_summary() -> List[Dict[str, Any]]:
    """Return only items that need reordering."""
    return [item for item in get_full_inventory() if item["needs_reorder"]]


def get_inventory_stats() -> Dict[str, Any]:
    """Return aggregate statistics for the dashboard."""
    inventory = get_full_inventory()
    total = len(inventory)
    low_stock = sum(1 for i in inventory if i["needs_reorder"])
    critical = sum(1 for i in inventory if i["is_critical"])
    total_value = sum(i["on_hand_qty"] * i["base_unit_price"] for i in inventory)
    return {
        "total_skus": total,
        "low_stock_count": low_stock,
        "critical_parts_count": critical,
        "total_inventory_value_usd": round(total_value, 2),
    }
