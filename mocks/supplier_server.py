"""
Supplier API Server
====================
FastAPI server that simulates 3 external supplier REST APIs.

Each supplier is mounted at its own path prefix:
    /supplier_a/...
    /supplier_b/...
    /supplier_c/...

Run:
    python -m mocks.supplier_server
    # or: uvicorn mocks.supplier_server:app --port 8001
"""

from __future__ import annotations

import asyncio
import logging
import random
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from mocks.suppliers import (
    MockSupplierAPI,
    SupplierCatalog,
    SupplierID,
    SupplierQuote,
)

logger = logging.getLogger("supplier_server")

# ---------------------------------------------------------------------------
# Boot-time: initialize supplier instances once
# ---------------------------------------------------------------------------

_SUPPLIERS: Dict[str, MockSupplierAPI] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create mock supplier instances on startup."""
    for sid in SupplierID:
        _SUPPLIERS[sid.value] = MockSupplierAPI(sid)
    logger.info("Supplier mock server ready — %d suppliers loaded", len(_SUPPLIERS))
    yield
    _SUPPLIERS.clear()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Mock Supplier API Gateway",
    description=(
        "Simulates 3 external supplier endpoints with distinct stock, "
        "pricing, and lead-time profiles."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

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
# Routes — Health
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health():
    """Check if the supplier server is up and which suppliers are loaded."""
    return HealthResponse(
        status="ok",
        suppliers=list(_SUPPLIERS.keys()),
    )


# ---------------------------------------------------------------------------
# Routes — Catalog
# ---------------------------------------------------------------------------

@app.get(
    "/{supplier_id}/catalog",
    response_model=SupplierCatalog,
    responses={404: {"model": ErrorResponse}},
    tags=["Catalog"],
    summary="Get full product catalog",
)
async def get_catalog(supplier_id: str):
    """Return the full product catalog for a supplier."""
    api = _SUPPLIERS.get(supplier_id)
    if api is None:
        raise HTTPException(status_code=404, detail=f"Unknown supplier: {supplier_id}")
    return await api.get_catalog()


# ---------------------------------------------------------------------------
# Routes — Quote
# ---------------------------------------------------------------------------

@app.get(
    "/{supplier_id}/quote",
    response_model=SupplierQuote,
    responses={404: {"model": ErrorResponse}},
    tags=["Quotes"],
    summary="Request a quote for a SKU",
)
async def get_quote(
    supplier_id: str,
    sku: str = Query(..., description="SKU code, e.g. SKU-MOTOR-001"),
    quantity: int = Query(1, ge=1, description="Desired quantity"),
):
    """
    Request a price quote including unit price, available stock,
    lead time, freight base rate, and speed factor.
    """
    api = _SUPPLIERS.get(supplier_id)
    if api is None:
        raise HTTPException(status_code=404, detail=f"Unknown supplier: {supplier_id}")
    quote = await api.get_quote(sku, quantity)
    if quote is None:
        raise HTTPException(status_code=404, detail=f"SKU not found: {sku}")
    return quote


# ---------------------------------------------------------------------------
# Routes — Stock Check
# ---------------------------------------------------------------------------

@app.get(
    "/{supplier_id}/stock/{sku}",
    response_model=StockCheckResponse,
    responses={404: {"model": ErrorResponse}},
    tags=["Stock"],
    summary="Check available stock for a SKU",
)
async def check_stock(supplier_id: str, sku: str):
    """Quick stock availability check for a single SKU."""
    api = _SUPPLIERS.get(supplier_id)
    if api is None:
        raise HTTPException(status_code=404, detail=f"Unknown supplier: {supplier_id}")
    qty = await api.check_stock(sku)
    if qty is None:
        raise HTTPException(status_code=404, detail=f"SKU not found: {sku}")
    return StockCheckResponse(
        supplier_id=supplier_id,
        sku=sku,
        available_qty=qty,
    )


# ---------------------------------------------------------------------------
# Routes — Fan-out (query all suppliers at once)
# ---------------------------------------------------------------------------

@app.get(
    "/quotes/all",
    response_model=list[SupplierQuote],
    tags=["Quotes"],
    summary="Fan-out quote request to all suppliers",
)
async def get_all_quotes(
    sku: str = Query(..., description="SKU code"),
    quantity: int = Query(1, ge=1, description="Desired quantity"),
):
    """Query all suppliers concurrently and return combined quotes."""
    tasks = [api.get_quote(sku, quantity) for api in _SUPPLIERS.values()]
    results = await asyncio.gather(*tasks)
    quotes = [r for r in results if r is not None]
    if not quotes:
        raise HTTPException(status_code=404, detail=f"SKU not found at any supplier: {sku}")
    return quotes


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "mocks.supplier_server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info",
    )
