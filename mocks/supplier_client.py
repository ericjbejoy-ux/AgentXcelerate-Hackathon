"""
Supplier API Client
====================
HTTP client that agents use to talk to the supplier mock server.

This is what your teammates import — it hits the FastAPI server over HTTP,
just like calling a real external supplier API.

Usage::

    from mocks.supplier_client import SupplierClient

    async with SupplierClient() as client:
        quote  = await client.get_quote("supplier_a", "SKU-MOTOR-001", quantity=10)
        quotes = await client.get_all_quotes("SKU-MOTOR-001", quantity=10)
        catalog = await client.get_catalog("supplier_b")
        stock  = await client.check_stock("supplier_c", "SKU-VALVE-003")
"""

from __future__ import annotations

import logging
import os
from typing import List, Optional

import requests
from pydantic import BaseModel

from mocks.suppliers import SupplierCatalog, SupplierQuote

logger = logging.getLogger("supplier_client")

# Default base URL — overridable via env var
_DEFAULT_BASE_URL = "http://localhost:8001"


class StockCheckResponse(BaseModel):
    supplier_id: str
    sku: str
    available_qty: int


class SupplierClient:
    """
    Synchronous + async HTTP client for the mock supplier server.

    Uses ``requests`` (already in requirements.txt) for simplicity.
    Agents call this instead of importing supplier classes directly.
    """

    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = (
            base_url
            or os.getenv("SUPPLIER_API_URL")
            or _DEFAULT_BASE_URL
        ).rstrip("/")

    # -- Context manager for clean usage -----------------------------------

    async def __aenter__(self) -> "SupplierClient":
        return self

    async def __aexit__(self, *args) -> None:
        pass

    # -- Health ------------------------------------------------------------

    def health(self) -> dict:
        """Check server health."""
        resp = requests.get(f"{self.base_url}/health", timeout=5)
        resp.raise_for_status()
        return resp.json()

    # -- Catalog -----------------------------------------------------------

    def get_catalog(self, supplier_id: str) -> SupplierCatalog:
        """Fetch full catalog from a supplier."""
        resp = requests.get(
            f"{self.base_url}/{supplier_id}/catalog", timeout=10,
        )
        resp.raise_for_status()
        return SupplierCatalog(**resp.json())

    # -- Quote -------------------------------------------------------------

    def get_quote(
        self,
        supplier_id: str,
        sku: str,
        quantity: int = 1,
    ) -> SupplierQuote:
        """Request a quote from a specific supplier."""
        resp = requests.get(
            f"{self.base_url}/{supplier_id}/quote",
            params={"sku": sku, "quantity": quantity},
            timeout=10,
        )
        resp.raise_for_status()
        return SupplierQuote(**resp.json())

    def get_all_quotes(
        self,
        sku: str,
        quantity: int = 1,
    ) -> List[SupplierQuote]:
        """Fan-out quote request to all suppliers via the server."""
        resp = requests.get(
            f"{self.base_url}/quotes/all",
            params={"sku": sku, "quantity": quantity},
            timeout=15,
        )
        resp.raise_for_status()
        return [SupplierQuote(**q) for q in resp.json()]

    # -- Stock Check -------------------------------------------------------

    def check_stock(self, supplier_id: str, sku: str) -> StockCheckResponse:
        """Quick stock check for a single SKU at a supplier."""
        resp = requests.get(
            f"{self.base_url}/{supplier_id}/stock/{sku}", timeout=10,
        )
        resp.raise_for_status()
        return StockCheckResponse(**resp.json())

    # -- Order Operations --------------------------------------------------

    def place_order(self, supplier_id: str, sku: str, quantity: int) -> dict:
        """Place an order with a supplier. Returns order receipt details."""
        resp = requests.post(
            f"{self.base_url}/{supplier_id}/order",
            json={"sku": sku, "quantity": quantity},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def cancel_order(self, order_id: str) -> dict:
        """Cancel an order by ID. Restores stock at the supplier."""
        resp = requests.post(
            f"{self.base_url}/orders/{order_id}/cancel",
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

