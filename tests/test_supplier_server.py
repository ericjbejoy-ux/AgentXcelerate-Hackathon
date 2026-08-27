"""
Integration Tests for Supplier HTTP Server, Client, and Logistics Pipeline.
"""

from __future__ import annotations

import multiprocessing
import time
import pytest
import uvicorn
import requests

from mocks.supplier_server import app
from mocks.supplier_client import SupplierClient

# Run mock supplier server on port 8002 in a separate process for integration tests
def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="warning")


@pytest.fixture(scope="module", autouse=True)
def supplier_server():
    proc = multiprocessing.Process(target=run_server, daemon=True)
    proc.start()
    # Wait for server to boot
    for _ in range(50):
        try:
            resp = requests.get("http://127.0.0.1:8002/health", timeout=0.1)
            if resp.status_code == 200:
                break
        except requests.exceptions.RequestException:
            pass
        time.sleep(0.1)
    else:
        pytest.fail("Supplier mock server failed to start on port 8002")
    
    yield
    proc.terminate()
    proc.join()


def test_client_health():
    client = SupplierClient(base_url="http://127.0.0.1:8002")
    health_data = client.health()
    assert health_data["status"] == "ok"
    assert "supplier_a" in health_data["suppliers"]


def test_client_catalog():
    client = SupplierClient(base_url="http://127.0.0.1:8002")
    catalog = client.get_catalog("supplier_a")
    assert catalog.supplier_id == "supplier_a"
    assert len(catalog.items) == 10


def test_client_get_quote():
    client = SupplierClient(base_url="http://127.0.0.1:8002")
    quote = client.get_quote("supplier_a", "SKU-MOTOR-001", quantity=3)
    assert quote.sku == "SKU-MOTOR-001"
    assert quote.available_qty > 0
    assert quote.supplier_id == "supplier_a"


def test_logistics_quote_endpoint():
    client = SupplierClient(base_url="http://127.0.0.1:8002")
    quote = client.get_freight_quote(
        origin="supplier_b",
        destination="ZONE-WEST",
        sku="SKU-MOTOR-001",
        quantity=5,
        transit_speed_mode="express"
    )
    assert quote.transit_speed_mode == "EXPRESS"
    assert quote.carrier_transit_days == 1.5
    assert quote.total_transit_days == 3.5
    assert quote.freight_cost > 0.0


def test_seller_order_placement_and_reallocation():
    client = SupplierClient(base_url="http://127.0.0.1:8002")
    sku = "SKU-MOTOR-001"
    
    # 1. Place a low priority buffer order to commit some stock
    low_order = client.place_seller_order(
        supplier_id="supplier_a",
        buyer_id="CLIENT-LOW-PRIO",
        sku=sku,
        quantity=3,
        priority="LOW"
    )
    assert low_order["priority"] == "LOW"
    
    # 2. Place a high-priority order that triggers a potential reallocation or direct check
    high_order = client.place_seller_order(
        supplier_id="supplier_a",
        buyer_id="CLIENT-HIGH-PRIO",
        sku=sku,
        quantity=5,
        priority="HIGH"
    )
    assert high_order["priority"] == "HIGH"
    assert high_order["gross_revenue"] > 0
    assert high_order["net_margin"] != 0
