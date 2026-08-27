"""
Supplier API Server
====================
FastAPI server that simulates 3 external supplier REST APIs.

Includes stock checks, quote requests, and order lifecycle management
(order placement, cancelation, and stateful inventory deduction).
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query, Body
from pydantic import BaseModel, Field

from mocks.suppliers import (
    MockSupplierAPI,
    SupplierCatalog,
    SupplierID,
    SupplierQuote,
)

logger = logging.getLogger("supplier_server")

# ---------------------------------------------------------------------------
# State Management (InMemory DB for Orders and Live Catalog State)
# ---------------------------------------------------------------------------

class OrderRecord(BaseModel):
    order_id: str
    supplier_id: str
    sku: str
    quantity: int
    unit_price: float
    total_cost: float
    status: str = "PENDING"  # PENDING, COMPLETED, CANCELLED
    created_at: str
    lead_time_days: float


_SUPPLIERS: Dict[str, MockSupplierAPI] = {}
_ORDERS: List[OrderRecord] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize mock suppliers on startup."""
    for sid in SupplierID:
        _SUPPLIERS[sid.value] = MockSupplierAPI(sid)
    logger.info("Supplier mock server ready — %d suppliers loaded", len(_SUPPLIERS))
    yield
    _SUPPLIERS.clear()
    _ORDERS.clear()


app = FastAPI(
    title="Mock Supplier API Gateway",
    description="Simulates 3 external supplier endpoints with order lifecycle management.",
    version="1.1.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------

class OrderCreateRequest(BaseModel):
    sku: str
    quantity: int = Field(..., ge=1)


class OrderResponse(BaseModel):
    order_id: str
    supplier_id: str
    sku: str
    quantity: int
    total_cost: float
    status: str
    created_at: str
    lead_time_days: float


class StockCheckResponse(BaseModel):
    supplier_id: str
    sku: str
    available_qty: int


class HealthResponse(BaseModel):
    status: str
    suppliers: list[str]


class ErrorResponse(BaseModel):
    detail: str


# ---------------------------------------------------------------------------
# Routes — Health & Orders Management
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health():
    return HealthResponse(status="ok", suppliers=list(_SUPPLIERS.keys()))


@app.get("/orders", response_model=List[OrderRecord], tags=["Orders"])
async def get_all_orders(supplier_id: Optional[str] = None):
    """Retrieve orders, optionally filtered by supplier."""
    if supplier_id:
        return [o for o in _ORDERS if o.supplier_id == supplier_id]
    return _ORDERS


# ---------------------------------------------------------------------------
# Routes — Catalog & Quotes
# ---------------------------------------------------------------------------

@app.get("/{supplier_id}/catalog", response_model=SupplierCatalog, tags=["Catalog"])
async def get_catalog(supplier_id: str):
    api = _SUPPLIERS.get(supplier_id)
    if api is None:
        raise HTTPException(status_code=404, detail=f"Unknown supplier: {supplier_id}")
    return await api.get_catalog()


@app.get("/{supplier_id}/quote", response_model=SupplierQuote, tags=["Quotes"])
async def get_quote(supplier_id: str, sku: str, quantity: int = 1):
    api = _SUPPLIERS.get(supplier_id)
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


# ---------------------------------------------------------------------------
# Routes — Order Lifecycle
# ---------------------------------------------------------------------------

@app.post("/{supplier_id}/order", response_model=OrderResponse, tags=["Orders"])
async def place_order(supplier_id: str, payload: OrderCreateRequest):
    """Place a purchase order and deduct stock from mock supplier catalog."""
    api = _SUPPLIERS.get(supplier_id)
    if api is None:
        raise HTTPException(status_code=404, detail=f"Unknown supplier: {supplier_id}")
    
    # Verify stock and pricing via quote
    quote = await api.get_quote(payload.sku, payload.quantity)
    if quote is None:
        raise HTTPException(status_code=404, detail=f"SKU not found: {payload.sku}")
    if not quote.in_stock:
        raise HTTPException(status_code=400, detail="Insufficient stock at supplier")
    
    # Deduct stock
    api._catalog[payload.sku].available_qty -= payload.quantity
    
    # Create order record
    order = OrderRecord(
        order_id=f"PO-{uuid.uuid4().hex[:6].upper()}",
        supplier_id=supplier_id,
        sku=payload.sku,
        quantity=payload.quantity,
        unit_price=quote.unit_price,
        total_cost=round(quote.unit_price * payload.quantity, 2),
        status="PENDING",
        created_at=datetime.utcnow().isoformat(),
        lead_time_days=quote.lead_time_days
    )
    _ORDERS.append(order)
    return order


@app.post("/orders/{order_id}/cancel", response_model=OrderResponse, tags=["Orders"])
async def cancel_order(order_id: str):
    """Cancel an active order and restore supplier stock."""
    order = next((o for o in _ORDERS if o.order_id == order_id), None)
    if order is None:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    if order.status == "CANCELLED":
        raise HTTPException(status_code=400, detail="Order is already cancelled")
        
    order.status = "CANCELLED"
    
    # Restore stock to supplier
    api = _SUPPLIERS.get(order.supplier_id)
    if api and order.sku in api._catalog:
         api._catalog[order.sku].available_qty += order.quantity
         
    return order


@app.get("/{supplier_id}/stock/{sku}", response_model=StockCheckResponse, tags=["Stock"])
async def check_stock(supplier_id: str, sku: str):
    api = _SUPPLIERS.get(supplier_id)
    if api is None:
        raise HTTPException(status_code=404, detail=f"Unknown supplier: {supplier_id}")
    qty = await api.check_stock(sku)
    if qty is None:
        raise HTTPException(status_code=404, detail=f"SKU not found: {sku}")
    return StockCheckResponse(supplier_id=supplier_id, sku=sku, available_qty=qty)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("mocks.supplier_server:app", host="0.0.0.0", port=8001, reload=True)
