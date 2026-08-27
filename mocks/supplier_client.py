"""
Supplier & Logistics API Client
===============================
HTTP client that agents use to query seller portals and logistics carriers.
"""

from __future__ import annotations

import os
from typing import List, Optional
import requests

from mocks.suppliers import SupplierCatalog, SupplierQuote
from mocks.logistics import FreightQuoteRequest, FreightQuoteResponse


class SupplierClient:
    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = (
            base_url
            or os.getenv("SUPPLIER_API_URL")
            or "http://localhost:8001"
        ).rstrip("/")

    def health(self) -> dict:
        resp = requests.get(f"{self.base_url}/health", timeout=5)
        resp.raise_for_status()
        return resp.json()

    # -- Catalog & Quotes --------------------------------------------------

    def get_catalog(self, supplier_id: str) -> SupplierCatalog:
        resp = requests.get(f"{self.base_url}/{supplier_id}/catalog", timeout=10)
        resp.raise_for_status()
        return SupplierCatalog(**resp.json())

    def get_quote(self, supplier_id: str, sku: str, quantity: int = 1) -> SupplierQuote:
        resp = requests.get(
            f"{self.base_url}/{supplier_id}/quote",
            params={"sku": sku, "quantity": quantity},
            timeout=10,
        )
        resp.raise_for_status()
        return SupplierQuote(**resp.json())

    def get_all_quotes(self, sku: str, quantity: int = 1) -> List[SupplierQuote]:
        resp = requests.get(
            f"{self.base_url}/quotes/all",
            params={"sku": sku, "quantity": quantity},
            timeout=15,
        )
        resp.raise_for_status()
        return [SupplierQuote(**q) for q in resp.json()]

    # -- Logistics Endpoints -----------------------------------------------

    def get_freight_quote(
        self,
        origin: str,
        destination: str,
        sku: str,
        quantity: int,
        transit_speed_mode: str = "standard",
    ) -> FreightQuoteResponse:
        """Query freight cost and transit times from the logistics API."""
        payload = FreightQuoteRequest(
            origin=origin,
            destination=destination,
            sku=sku,
            quantity=quantity,
            transit_speed_mode=transit_speed_mode
        )
        resp = requests.post(f"{self.base_url}/logistics/quote", json=payload.model_dump(), timeout=10)
        resp.raise_for_status()
        return FreightQuoteResponse(**resp.json())

    # -- Seller Order Operations -------------------------------------------

    def place_seller_order(
        self,
        supplier_id: str,
        buyer_id: str,
        sku: str,
        quantity: int,
        priority: str = "MEDIUM",
        destination_zone: str = "ZONE-EAST",
        transit_speed_mode: str = "standard"
    ) -> dict:
        """Place an order with the supplier. Initiates priorities and reallocations."""
        payload = {
            "buyer_id": buyer_id,
            "sku": sku,
            "quantity": quantity,
            "priority": priority,
            "destination_zone": destination_zone,
            "transit_speed_mode": transit_speed_mode
        }
        resp = requests.post(
            f"{self.base_url}/seller/{supplier_id}/order",
            json=payload,
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    def list_seller_orders(self, supplier_id: Optional[str] = None) -> List[dict]:
        """List incoming orders placed on the seller gateway."""
        params = {}
        if supplier_id:
            params["supplier_id"] = supplier_id
        resp = requests.get(f"{self.base_url}/seller/orders", params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def cancel_seller_order(self, order_id: str) -> dict:
        """Cancel order and restore stock."""
        resp = requests.post(f"{self.base_url}/seller/orders/{order_id}/cancel", timeout=10)
        resp.raise_for_status()
        return resp.json()
