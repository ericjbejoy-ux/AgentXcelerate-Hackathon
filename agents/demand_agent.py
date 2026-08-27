import logging
import math
from core.database import db
from mocks.suppliers import query_all_suppliers, get_all_supplier_apis, SupplierID, MockSupplierAPI
from mocks.logistics import calculate_freight_quote
import asyncio

logger = logging.getLogger("demand_agent")

# Region → logistics zone mapping
_REGION_TO_ZONE = {
    "East": "ZONE-EAST",
    "West": "ZONE-WEST",
    "South": "ZONE-CENTRAL",
    "North": "ZONE-CENTRAL",
    "Central": "ZONE-CENTRAL",
    "Northeast": "ZONE-EAST",
}


def _build_warehouse_candidates(order: dict) -> list:
    part_id = order.get("part_id", "")
    requested_qty = order.get("requested_qty", 1)
    max_lead = order.get("max_lead_time_days", 999)
    priority = order.get("priority", "MEDIUM").upper()
    candidates = []

    if requested_qty <= 0:
        logger.warning("[WAREHOUSE] requested_qty=%d is invalid, skipping", requested_qty)
        return candidates
    if max_lead <= 0:
        max_lead = 999

    logger.info("[WAREHOUSE] Looking up SKU=%s across all warehouses (requested=%d, max_lead=%dd)", part_id, requested_qty, max_lead)
    all_stocks = db.inventory.get_all_stocks(part_id)
    if not all_stocks:
        logger.info("[WAREHOUSE] SKU=%s not found in any warehouse", part_id)
        return candidates

    logger.info("[WAREHOUSE] Found %d warehouse locations for SKU=%s", len(all_stocks), part_id)

    sku_record = db.inventory.get_sku(part_id)
    unit_price = sku_record.base_unit_price if sku_record else 100.0

    for stock in all_stocks:
        if stock.available_qty <= 0:
            continue

        wh = db.inventory.get_warehouse(stock.warehouse_loc)
        lead_time = wh.base_lead_days if wh else 2
        wh_reliability = wh.reliability if wh else 0.95

        fulfilled = min(requested_qty, stock.available_qty)

        # Reliability based on warehouse reliability + lead time constraint
        reliability = wh_reliability
        if lead_time > max_lead:
            overage = (lead_time - max_lead) / max_lead
            reliability *= max(0.3, 1.0 - overage)

        # Partial fill penalty
        if fulfilled < requested_qty:
            fill_ratio = fulfilled / requested_qty
            reliability *= fill_ratio

        total_cost = round(unit_price * fulfilled, 2)
        candidates.append({
            "option_id": f"WH-{stock.warehouse_loc}",
            "strategy_name": f"Warehouse ({wh.warehouse_name if wh else stock.warehouse_loc})",
            "source": stock.warehouse_loc,
            "fulfilled_qty": fulfilled,
            "unit_cost": round(unit_price, 2),
            "total_cost": total_cost,
            "lead_time_days": lead_time,
            "reliability_score": round(reliability, 2),
            "warehouse_id": stock.warehouse_loc,
        })

    logger.info("[WAREHOUSE] Generated %d warehouse candidates", len(candidates))
    return candidates


def _build_supplier_candidates(order: dict) -> list:
    part_id = order.get("part_id", "")
    requested_qty = order.get("requested_qty", 1)
    max_lead = order.get("max_lead_time_days", 999)
    priority = order.get("priority", "MEDIUM").upper()
    candidates = []

    if requested_qty <= 0:
        return candidates
    if max_lead <= 0:
        max_lead = 999

    logger.info("[SUPPLIER] Querying suppliers for SKU=%s qty=%d (max_lead=%dd)...", part_id, requested_qty, max_lead)
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                quotes = pool.submit(
                    asyncio.run, query_all_suppliers(part_id, requested_qty)
                ).result()
        else:
            quotes = asyncio.run(query_all_suppliers(part_id, requested_qty))
    except Exception as e:
        logger.warning("[SUPPLIER] Failed to query suppliers: %s", e)
        quotes = []

    # Get supplier profiles for freight calculation
    supplier_apis = get_all_supplier_apis()
    sku_record = db.inventory.get_sku(part_id)
    weight_kg = sku_record.weight_kg if sku_record else 1.0

    for quote in quotes:
        fulfilled = min(requested_qty, quote.available_qty)

        # Calculate real lead time via logistics formula
        supplier_api = supplier_apis.get(quote.supplier_id)
        handling_days = supplier_api.lead_time_days if supplier_api else quote.lead_time_days
        freight_rate = supplier_api.freight_base_rate if supplier_api else quote.freight_base_rate
        speed_factor = supplier_api.speed_factor if supplier_api else quote.speed_factor

        # Use express for CRITICAL/HIGH, standard for MEDIUM/LOW
        speed_mode = "express" if priority in ("CRITICAL", "HIGH") else "standard"

        freight = calculate_freight_quote(
            origin=quote.supplier_id,
            destination="ZONE-EAST",
            weight_kg=weight_kg,
            quantity=fulfilled,
            speed_mode=speed_mode,
            supplier_handling_days=handling_days,
            base_freight_rate=freight_rate,
            speed_factor_val=speed_factor,
        )

        lead_time = int(math.ceil(freight.total_transit_days))
        freight_cost = freight.freight_cost
        total_cost = round(quote.unit_price * fulfilled + freight_cost, 2)

        logger.info("[SUPPLIER] %s: speed=%s lead=%dd (h=%.0f+c=%.1f) freight=$%.2f",
                     quote.supplier_name, speed_mode, lead_time, freight.supplier_handling_days,
                     freight.carrier_transit_days, freight_cost)

        reliability = 0.90

        if lead_time > max_lead:
            overage = (lead_time - max_lead) / max_lead
            reliability *= max(0.3, 1.0 - overage)

        if not quote.in_stock:
            reliability *= 0.5
        elif fulfilled < requested_qty:
            fill_ratio = fulfilled / requested_qty
            reliability *= fill_ratio

        if priority == "CRITICAL" and lead_time > 3:
            reliability *= 0.6
        elif priority == "HIGH" and lead_time > 5:
            reliability *= 0.75

        candidates.append({
            "option_id": f"SUP-{quote.supplier_id}",
            "strategy_name": f"Supplier Order ({quote.supplier_name})",
            "source": quote.supplier_id,
            "fulfilled_qty": fulfilled,
            "unit_cost": round(quote.unit_price, 2),
            "total_cost": total_cost,
            "lead_time_days": lead_time,
            "reliability_score": round(reliability, 2),
            "warehouse_id": None,
        })

    return candidates


def _calculate_priority_weights(priority: str) -> dict:
    weights = {
        "CRITICAL": {"cost": 0.10, "lead_time": 0.60, "reliability": 0.30},
        "HIGH": {"cost": 0.20, "lead_time": 0.50, "reliability": 0.30},
        "MEDIUM": {"cost": 0.35, "lead_time": 0.35, "reliability": 0.30},
        "LOW": {"cost": 0.55, "lead_time": 0.15, "reliability": 0.30},
    }
    return weights.get(priority.upper(), weights["MEDIUM"])


def process_demand_layer(order: dict) -> dict:
    logger.info("="*60)
    logger.info("[DEMAND] RECEIVED ORDER: part=%s qty=%d priority=%s max_lead=%dd customer=%s",
                 order.get("part_id"), order.get("requested_qty", 0),
                 order.get("priority"), order.get("max_lead_time_days", 999),
                 order.get("customer_id"))

    candidates = _build_warehouse_candidates(order)
    candidates.extend(_build_supplier_candidates(order))

    if not candidates:
        logger.warning("[DEMAND] NO CANDIDATES FOUND — using emergency fallback")
        sku_record = db.inventory.get_sku(order.get("part_id", ""))
        unit_cost = sku_record.base_unit_price * 1.5 if sku_record else 200.0
        candidates.append({
            "option_id": "FALLBACK-EMERGENCY",
            "strategy_name": "Emergency Supplier Fallback",
            "source": "emergency_supplier",
            "fulfilled_qty": order.get("requested_qty", 1),
            "unit_cost": round(unit_cost, 2),
            "total_cost": round(unit_cost * order.get("requested_qty", 1), 2),
            "lead_time_days": 7,
            "reliability_score": 0.60,
            "warehouse_id": None,
        })

    weights = _calculate_priority_weights(order.get("priority", "MEDIUM"))
    logger.info("[DEMAND] TRANSMITTING %d candidates to RankingEngine with weights=%s", len(candidates), weights)
    logger.info("="*60)
    return {"order": order, "candidates": candidates, "weights": weights}
