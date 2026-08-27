import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from mocks.inventory_db import WAREHOUSE_STOCK, SKU_CATALOG
from core.topsis_solver import run_topsis_optimization
from agents.explanation_agent import generate_recommendation_rationale


def run_pipeline(order_payload: dict) -> dict:
    """
    Execute the full supply chain optimization pipeline.
    Builds candidates from inventory DB + runs TOPSIS + generates explanation.
    """
    try:
        requested_qty = int(order_payload.get("requested_qty", order_payload.get("quantity", 1)))
        priority = order_payload.get("priority", "MEDIUM").upper()

        # Build candidates from warehouse stock
        candidates = []
        for sku_key, stock in WAREHOUSE_STOCK.items():
            rec = SKU_CATALOG.get(sku_key)
            if rec is None:
                continue
            candidates.append({
                "candidate_id": f"WH-{sku_key[-3:]}",
                "warehouse_id": stock.warehouse_loc,
                "warehouse_loc": stock.warehouse_loc,
                "item_sku": sku_key,
                "description": rec.description,
                "source": "Internal Warehouse",
                "available_stock": stock.available_qty,
                "current_stock": stock.on_hand_qty,
                "allocated_stock": stock.reserved_qty,
                "remaining_stock": stock.available_qty,
                "unit_cost": rec.base_unit_price,
                "total_cost": round(rec.base_unit_price * requested_qty, 2),
                "lead_time_days": 2,
                "reliability_score": 0.97,
                "distance": 50,
                "can_fulfill": stock.available_qty >= requested_qty,
                "fulfillment_type": "Direct Warehouse Stock",
            })

        # Priority → weights
        _weights = {
            "LOW":      {"cost": 0.40, "lead_time": 0.20, "reliability": 0.25, "distance": 0.15},
            "MEDIUM":   {"cost": 0.25, "lead_time": 0.35, "reliability": 0.30, "distance": 0.10},
            "HIGH":     {"cost": 0.15, "lead_time": 0.50, "reliability": 0.25, "distance": 0.10},
            "CRITICAL": {"cost": 0.10, "lead_time": 0.60, "reliability": 0.20, "distance": 0.10},
        }
        weights = order_payload.get("weights", _weights.get(priority, _weights["MEDIUM"]))

        results = run_topsis_optimization(candidates, weights)
        top_winner = results[0] if results else {}
        rationale = generate_recommendation_rationale(order_payload, top_winner, weights)

        return {
            "status": "success",
            "top_strategy": top_winner,
            "explanation": rationale,
            "candidate_strategies": results,
            "criteria_weights": weights,
        }
    except Exception as e:
        return {"error": str(e)}
