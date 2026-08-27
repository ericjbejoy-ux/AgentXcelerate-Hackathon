"""
Mock Supplier API Interfaces
=============================
Three distinct supplier profiles with stock, pricing, and lead-time characteristics.

Supplier A (Primary)    — Full stock, low cost, long lead time (10 days)
Supplier B (Express)    — Partial stock, high cost, fast lead time (2 days)
Supplier C (Alt Region) — Medium stock, medium cost, variable freight (4 days)
"""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from mocks.inventory_db import SKU_CATALOG

# ---------------------------------------------------------------------------
# Pydantic models (shared contract)
# ---------------------------------------------------------------------------


class SupplierID(str, Enum):
    A = "supplier_a"
    B = "supplier_b"
    C = "supplier_c"


class StockItem(BaseModel):
    """A single SKU entry in a supplier's catalog."""

    sku: str
    description: str
    unit_price: float = Field(ge=0, description="Price per unit in USD")
    available_qty: int = Field(ge=0, description="Units currently in stock")


class SupplierQuote(BaseModel):
    """Response from a supplier availability / quote query."""

    supplier_id: str
    supplier_name: str
    sku: str
    unit_price: float
    available_qty: int
    lead_time_days: float = Field(description="Nominal lead time in calendar days")
    in_stock: bool
    freight_base_rate: float = Field(description="Base freight cost in USD")
    speed_factor: float = Field(description="Exponential speed multiplier for freight")


class SupplierCatalog(BaseModel):
    """Full catalog snapshot from a supplier."""

    supplier_id: str
    supplier_name: str
    items: list[StockItem]
    lead_time_days: float
    freight_base_rate: float
    speed_factor: float


# ---------------------------------------------------------------------------
# Derive catalog data from the centralized inventory database
# ---------------------------------------------------------------------------

# Build catalog template and base prices from the single source of truth
_CATALOG_TEMPLATE: Dict[str, StockItem] = {
    sku: StockItem(
        sku=sku,
        description=record.description,
        unit_price=0.0,  # overridden per supplier
        available_qty=0,
    )
    for sku, record in SKU_CATALOG.items()
}

_BASE_PRICES: Dict[str, float] = {
    sku: record.base_unit_price for sku, record in SKU_CATALOG.items()
}


@dataclass
class _SupplierProfile:
    """Internal definition of a mock supplier."""

    supplier_id: SupplierID
    name: str
    lead_time_days: float
    freight_base_rate: float
    speed_factor: float
    price_multiplier: float  # applied to a base price
    stock_ratio: float  # fraction of max stock available (0.0–1.0)
    base_prices: Dict[str, float] = field(default_factory=dict)
    max_stock: int = 500

    def build_catalog(self) -> Dict[str, StockItem]:
        items: Dict[str, StockItem] = {}
        for sku, template in _CATALOG_TEMPLATE.items():
            base = self.base_prices.get(sku, 100.0)
            qty = int(self.max_stock * self.stock_ratio)
            # Add slight per-SKU randomness for realism
            qty = max(0, qty + random.randint(-20, 20))
            items[sku] = StockItem(
                sku=sku,
                description=template.description,
                unit_price=round(base * self.price_multiplier, 2),
                available_qty=qty,
            )
        return items


_PROFILES: Dict[SupplierID, _SupplierProfile] = {
    SupplierID.A: _SupplierProfile(
        supplier_id=SupplierID.A,
        name="Supplier A (Primary)",
        lead_time_days=10.0,
        freight_base_rate=50.0,
        speed_factor=0.3,  # low — standard shipping
        price_multiplier=1.0,  # cheapest
        stock_ratio=1.0,  # full stock
        base_prices=_BASE_PRICES,
    ),
    SupplierID.B: _SupplierProfile(
        supplier_id=SupplierID.B,
        name="Supplier B (Express)",
        lead_time_days=2.0,
        freight_base_rate=120.0,
        speed_factor=1.8,  # high — express premium
        price_multiplier=1.45,  # 45 % markup
        stock_ratio=0.35,  # partial stock
        base_prices=_BASE_PRICES,
    ),
    SupplierID.C: _SupplierProfile(
        supplier_id=SupplierID.C,
        name="Supplier C (Alt Region)",
        lead_time_days=4.0,
        freight_base_rate=80.0,
        speed_factor=1.0,  # moderate
        price_multiplier=1.15,  # 15 % markup
        stock_ratio=0.60,  # medium stock
        base_prices=_BASE_PRICES,
    ),
}


# ---------------------------------------------------------------------------
# Mock Supplier API class
# ---------------------------------------------------------------------------


class MockSupplierAPI:
    """
    Async mock API representing a single supplier endpoint.

    Usage::

        api = MockSupplierAPI(SupplierID.A)
        quote = await api.get_quote("SKU-MOTOR-001", quantity=10)
        catalog = await api.get_catalog()
    """

    def __init__(self, supplier_id: SupplierID) -> None:
        self._profile = _PROFILES[supplier_id]
        self._catalog = self._profile.build_catalog()

    @property
    def supplier_id(self) -> str:
        return self._profile.supplier_id.value

    @property
    def supplier_name(self) -> str:
        return self._profile.name

    @property
    def lead_time_days(self) -> float:
        return self._profile.lead_time_days

    @property
    def freight_base_rate(self) -> float:
        return self._profile.freight_base_rate

    @property
    def speed_factor(self) -> float:
        return self._profile.speed_factor

    async def get_catalog(self) -> SupplierCatalog:
        """Return the full catalog for this supplier (simulates network delay)."""
        await asyncio.sleep(random.uniform(0.05, 0.15))  # mock latency
        return SupplierCatalog(
            supplier_id=self.supplier_id,
            supplier_name=self.supplier_name,
            items=list(self._catalog.values()),
            lead_time_days=self.lead_time_days,
            freight_base_rate=self.freight_base_rate,
            speed_factor=self.speed_factor,
        )

    async def get_quote(self, sku: str, quantity: int = 1) -> SupplierQuote | None:
        """
        Request a quote for a specific SKU and quantity.

        Returns ``None`` if the SKU is unknown.
        """
        await asyncio.sleep(random.uniform(0.05, 0.15))
        item = self._catalog.get(sku)
        if item is None:
            return None
        return SupplierQuote(
            supplier_id=self.supplier_id,
            supplier_name=self.supplier_name,
            sku=item.sku,
            unit_price=item.unit_price,
            available_qty=item.available_qty,
            lead_time_days=self.lead_time_days,
            in_stock=item.available_qty >= quantity,
            freight_base_rate=self.freight_base_rate,
            speed_factor=self.speed_factor,
        )

    async def check_stock(self, sku: str) -> int | None:
        """Return current available quantity for a SKU, or ``None`` if unknown."""
        await asyncio.sleep(random.uniform(0.02, 0.08))
        item = self._catalog.get(sku)
        return item.available_qty if item else None


# ---------------------------------------------------------------------------
# Convenience: pre-built API instances
# ---------------------------------------------------------------------------


def get_all_supplier_apis() -> dict[str, MockSupplierAPI]:
    """Return a dict of ``{supplier_id: MockSupplierAPI}`` for all suppliers."""
    return {sid.value: MockSupplierAPI(sid) for sid in SupplierID}


async def query_all_suppliers(
    sku: str,
    quantity: int = 1,
) -> list[SupplierQuote]:
    """Fan-out a quote request to every supplier concurrently."""
    apis = get_all_supplier_apis()
    tasks = [api.get_quote(sku, quantity) for api in apis.values()]
    results = await asyncio.gather(*tasks)
    return [r for r in results if r is not None]
