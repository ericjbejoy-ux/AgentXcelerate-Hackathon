"""
Stateful Supplier & Logistics API Server
=========================================
Exposes two groups of REST endpoints:
1. Seller Endpoints (/seller/*): Handles incoming buyer requests, stock deductions, margins, and priority-based order reallocations.
2. Logistics Endpoints (/logistics/*): Computes dynamic freight rates, transit weights, and shipping speed routes.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from mocks.suppliers import MockSupplierAPI, SupplierID, SupplierCatalog, SupplierQuote
from mocks.logistics import calculate_freight_quote, FreightQuoteRequest, FreightQuoteResponse
from core.database import db

logger = logging.getLogger("supplier_server")

# ---------------------------------------------------------------------------
# Stateful In-Memory DB
# ---------------------------------------------------------------------------

class SellerOrderRecord(BaseModel):
    # Demand Signal
    incoming_order_id: str
    buyer_id: str
    part_id: str
    requested_qty: int
    priority: str = "MEDIUM"  # LOW, MEDIUM, HIGH
    
    # Inventory Impact
    current_stock: int
    allocated_stock: int
    remaining_stock: int
    warehouse_loc: str
    
    # Fulfillment Route
    fulfillment_type: str = "Direct Stock"  # Direct Stock, Production Run, Tier-2 Supplier
    
    # Client Reallocation Alerts
    deprioritized_order_id: Optional[str] = None
    affected_customer: Optional[str] = None
    sla_penalty: float = 0.0
    
    # Financial Margins
    gross_revenue: float
    fulfillment_cost: float
    expedited_freight_cost: float
    net_margin: float
    
    # Operational Directives
    recommended_action: str
    automated_approval_status: str = "APPROVED"  # APPROVED, PENDING_SIGN_OFF
    created_at: str


_SUPPLIERS: Dict[str, MockSupplierAPI] = {}
_SELLER_ORDERS: List[SellerOrderRecord] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize mock suppliers on startup."""
    for sid in SupplierID:
        _SUPPLIERS[sid.value] = MockSupplierAPI(sid)
    logger.info("Mock Supplier and Logistics Server Online")
    yield
    _SUPPLIERS.clear()
    _SELLER_ORDERS.clear()


app = FastAPI(
    title="Autonomous Supply Chain — Seller & Logistics Gateways",
    description="Mock APIs representing external seller platforms and logistics carriers.",
    version="1.2.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Seller View: Order Creation Payload
# ---------------------------------------------------------------------------

class PlaceOrderPayload(BaseModel):
    buyer_id: str = Field(..., example="CLIENT-NEXUS-9")
    sku: str = Field(..., example="SKU-MOTOR-001")
    quantity: int = Field(..., ge=1)
    priority: str = Field("MEDIUM", description="LOW, MEDIUM, or HIGH")
    destination_zone: str = Field("ZONE-EAST")
    transit_speed_mode: str = Field("standard")


class OrderCancelResponse(BaseModel):
    message: str
    cancelled_order_id: str
    restored_stock: int


# ---------------------------------------------------------------------------
# Routes: Logistics Carrier API
# ---------------------------------------------------------------------------

@app.post(
    "/logistics/quote",
    response_model=FreightQuoteResponse,
    tags=["Logistics"],
    summary="Retrieve realistic shipping times & freight rates",
)
async def get_freight_quote(payload: FreightQuoteRequest):
    """
    Query carrier rates and delivery times for a given origin, destination,
    and product weight profile.
    """
    supplier_api = _SUPPLIERS.get(payload.origin.lower())
    if not supplier_api:
        raise HTTPException(status_code=404, detail=f"Supplier {payload.origin} not found")
        
    sku_data = db.inventory.get_sku(payload.sku)
    if not sku_data:
        raise HTTPException(status_code=404, detail=f"SKU {payload.sku} not found")
        
    # Execute shipping calculation
    quote = calculate_freight_quote(
        origin=payload.origin,
        destination=payload.destination,
        weight_kg=sku_data.weight_kg,
        quantity=payload.quantity,
        speed_mode=payload.transit_speed_mode,
        supplier_handling_days=supplier_api.lead_time_days,
        base_freight_rate=supplier_api.freight_base_rate,
        speed_factor_val=supplier_api.speed_factor
    )
    return quote


# ---------------------------------------------------------------------------
# Routes: Seller & Inventory API
# ---------------------------------------------------------------------------

@app.get("/seller/orders", response_model=List[SellerOrderRecord], tags=["Seller"])
async def list_seller_orders(supplier_id: Optional[str] = None):
    """View incoming buyer orders, allocations, margins, and reallocations."""
    if supplier_id:
        # Match supplier_id with buyer order structures
        return [o for o in _SELLER_ORDERS if o.recommended_action.lower().find(supplier_id.lower()) != -1]
    return _SELLER_ORDERS


@app.post(
    "/seller/{supplier_id}/order",
    response_model=SellerOrderRecord,
    tags=["Seller"],
    summary="Submit a purchase order request to a supplier",
)
async def create_seller_order(supplier_id: str, payload: PlaceOrderPayload):
    """
    Evaluates stock commitments, executes reallocations for high-priority orders,
    calculates transaction margins, and registers the order.
    """
    api = _SUPPLIERS.get(supplier_id.lower())
    if not api:
        raise HTTPException(status_code=404, detail=f"Unknown supplier: {supplier_id}")
        
    sku_data = db.inventory.get_sku(payload.sku)
    if not sku_data:
        raise HTTPException(status_code=404, detail=f"SKU not found in master catalog: {payload.sku}")
        
    # Find supplier unit price
    supplier_quote = await api.get_quote(payload.sku, payload.quantity)
    if not supplier_quote:
        raise HTTPException(status_code=404, detail="SKU catalog record missing at supplier")
        
    current_avail = supplier_quote.available_qty
    allocated = 0
    fulfillment_route = "Direct Stock"
    reallocation_triggered = False
    deprioritized_id = None
    affected_cust = None
    sla_penalty_fee = 0.0
    action_directive = f"Dispatched {payload.quantity} of {payload.sku} from {supplier_id} catalog."
    automated_approval = "APPROVED"

    # Handle Stock Scenarios
    if current_avail >= payload.quantity:
        # Scenario A: Plenty of stock
        allocated = payload.quantity
        api._catalog[payload.sku].available_qty -= payload.quantity
    else:
        # Scenario B: Insufficient stock. Check priority for stock hijack / reallocation
        if payload.priority.upper() in ("HIGH", "CRITICAL"):
            # Search for a lower-priority order to hijack stock from (match by part_id)
            lower_priority_order = next(
                (o for o in _SELLER_ORDERS
                 if o.part_id == payload.sku
                 and o.priority in ("LOW", "MEDIUM")
                 and o.automated_approval_status == "APPROVED"),
                None
            )
            if lower_priority_order:
                # Hijack stock from lower priority buffer
                reallocation_triggered = True
                deprioritized_id = lower_priority_order.incoming_order_id
                affected_cust = lower_priority_order.buyer_id
                sla_penalty_fee = round(lower_priority_order.gross_revenue * 0.10, 2)  # 10% SLA penalty

                # Take stock
                allocated = payload.quantity
                # Deduct rest from supplier catalog
                needed_from_cat = max(0, payload.quantity - lower_priority_order.requested_qty)
                api._catalog[payload.sku].available_qty = max(0, api._catalog[payload.sku].available_qty - needed_from_cat)

                action_directive = f"Stock reallocated from lower-priority PO {deprioritized_id}."
            else:
                # No orders to hijack from. Fall back to production run or tier-2 supplier
                fulfillment_route = "Production Run"
                allocated = payload.quantity
                action_directive = "Insufficient stock. Initiated expedited production run."
                automated_approval = "PENDING_SIGN_OFF"

        else:
            # Low/Medium priority order with insufficient stock gets waitlisted
            fulfillment_route = "Tier-2 Supplier"
            allocated = current_avail
            api._catalog[payload.sku].available_qty = 0
            action_directive = "Fulfillment routed to Tier-2 backup supplier."
            automated_approval = "PENDING_SIGN_OFF"

    # Calculate financial margins
    gross_rev = round(supplier_quote.unit_price * payload.quantity, 2)
    fulfillment_base = round(gross_rev * 0.60, 2)  # 60% fulfillment cost
    
    # Calculate freight component via logistics function
    freight_calc = calculate_freight_quote(
        origin=supplier_id,
        destination=payload.destination_zone,
        weight_kg=sku_data.weight_kg,
        quantity=payload.quantity,
        speed_mode=payload.transit_speed_mode,
        supplier_handling_days=api.lead_time_days,
        base_freight_rate=api.freight_base_rate,
        speed_factor_val=api.speed_factor
    )
    freight_cost = freight_calc.freight_cost
    expedited_cost = freight_cost if payload.transit_speed_mode.lower() == "express" else 0.0
    
    net_margin = round(gross_rev - (fulfillment_base + freight_cost + sla_penalty_fee), 2)

    order_record = SellerOrderRecord(
        incoming_order_id=f"PO-{uuid.uuid4().hex[:6].upper()}",
        buyer_id=payload.buyer_id,
        part_id=payload.sku,
        requested_qty=payload.quantity,
        priority=payload.priority.upper(),
        current_stock=current_avail,
        allocated_stock=allocated,
        remaining_stock=max(0, current_avail - allocated),
        warehouse_loc=getattr(sku_data, "warehouse_loc", "WH-DIST-01"),
        fulfillment_type=fulfillment_route,
        deprioritized_order_id=deprioritized_id,
        affected_customer=affected_cust,
        sla_penalty=sla_penalty_fee,
        gross_revenue=gross_rev,
        fulfillment_cost=fulfillment_base,
        expedited_freight_cost=expedited_cost,
        net_margin=net_margin,
        recommended_action=action_directive,
        automated_approval_status=automated_approval,
        created_at=datetime.utcnow().isoformat()
    )
    
    # Store order reference locally for supplier_id tracking helper
    # To keep simple schema but allow query filters, attach supplier_id temporarily
    order_dict = order_record.model_dump()
    order_record_with_meta = SellerOrderRecord(**order_dict)
    # Store reference with supplier_id injected dynamically
    order_record_with_meta.recommended_action = f"[{supplier_id.upper()}] " + order_record.recommended_action
    
    _SELLER_ORDERS.append(order_record_with_meta)
    return order_record_with_meta


@app.post(
    "/seller/orders/{order_id}/cancel",
    response_model=OrderCancelResponse,
    tags=["Seller"],
)
async def cancel_seller_order(order_id: str):
    """Cancel an active seller order and restore inventory."""
    idx = next((i for i, o in enumerate(_SELLER_ORDERS) if o.incoming_order_id == order_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Order not found")
        
    order = _SELLER_ORDERS.pop(idx)
    
    # Try to restore stock to supplier catalog
    # Extrapolate supplier name from recommended action metadata e.g. [SUPPLIER_A]
    supplier_tag = "supplier_a"
    if "[" in order.recommended_action:
        supplier_tag = order.recommended_action.split("]")[0].replace("[", "").lower()
        
    api = _SUPPLIERS.get(supplier_tag)
    if api and order.part_id in api._catalog:
        api._catalog[order.part_id].available_qty += order.allocated_stock
        
    return OrderCancelResponse(
        message="Order cancelled successfully.",
        cancelled_order_id=order_id,
        restored_stock=order.allocated_stock
    )


# ---------------------------------------------------------------------------
# Backwards Compatible Catalog & Health Routes
# ---------------------------------------------------------------------------

@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "suppliers": list(_SUPPLIERS.keys())}


@app.get("/{supplier_id}/catalog", response_model=SupplierCatalog, tags=["Catalog"])
async def get_catalog(supplier_id: str):
    api = _SUPPLIERS.get(supplier_id.lower())
    if api is None:
        raise HTTPException(status_code=404, detail=f"Unknown supplier: {supplier_id}")
    return await api.get_catalog()


@app.get("/{supplier_id}/quote", response_model=SupplierQuote, tags=["Quotes"])
async def get_quote(supplier_id: str, sku: str, quantity: int = 1):
    api = _SUPPLIERS.get(supplier_id.lower())
    if api is None:
        raise HTTPException(status_code=404, detail=f"Unknown supplier: {supplier_id}")
    quote = await api.get_quote(sku, quantity)
    if quote is None:
        raise HTTPException(status_code=404, detail=f"SKU not found: {sku}")
    return quote


@app.get("/quotes/all", response_model=List[SupplierQuote], tags=["Quotes"])
async def get_all_quotes(sku: str, quantity: int = 1):
    tasks = [api.get_quote(sku, quantity) for api in _SUPPLIERS.values()]
    results = await asyncio.gather(*tasks)
    quotes = [r for r in results if r is not None]
    return quotes


@app.get("/{supplier_id}/stock/{sku}", tags=["Stock"])
async def check_stock(supplier_id: str, sku: str):
    api = _SUPPLIERS.get(supplier_id.lower())
    if api is None:
        raise HTTPException(status_code=404, detail=f"Unknown supplier: {supplier_id}")
    qty = await api.check_stock(sku)
    if qty is None:
        raise HTTPException(status_code=404, detail=f"SKU not found: {sku}")
    return {"supplier_id": supplier_id, "sku": sku, "available_qty": qty}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("mocks.supplier_server:app", host="0.0.0.0", port=8001, reload=True)
