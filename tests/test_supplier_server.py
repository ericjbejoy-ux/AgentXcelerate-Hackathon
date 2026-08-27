"""
Tests for Supplier HTTP Server, Client, and Logistics Pipeline.
"""

from __future__ import annotations

import multiprocessing
import time
import pytest
import uvicorn
import requests

from mocks.supplier_server import app
from mocks.supplier_client import SupplierClient
from mocks.logistics import build_cost_breakdown, filter_by_lead_time

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


def test_client_get_all_quotes_and_logistics_pipeline():
    client = SupplierClient(base_url="http://127.0.0.1:8002")
    # 1. Fetch quotes from all suppliers over HTTP
    quotes = client.get_all_quotes("SKU-MOTOR-001", quantity=5)
    assert len(quotes) == 3
    
    # 2. Build landed cost breakdowns
    breakdowns = [build_cost_breakdown(q, 5) for q in quotes]
    assert len(breakdowns) == 3
    
    # 3. Filter using constraint verifier (max 5 days lead time)
    # Supplier A should be rejected (10 days), B and C should be viable
    result = filter_by_lead_time(breakdowns, max_lead_time_days=5.0)
    
    viable_ids = {v.supplier_id for v in result.viable}
    rejected_ids = {r.supplier_id for r in result.rejected}
    
    assert "supplier_a" in rejected_ids
    assert "supplier_b" in viable_ids
    assert "supplier_c" in viable_ids


def test_order_placement_and_cancelation():
    client = SupplierClient(base_url="http://127.0.0.1:8002")
    sku = "SKU-MOTOR-001"
    
    # Get initial stock
    initial_stock = client.check_stock("supplier_a", sku).available_qty
    
    # 1. Place order
    order = client.place_order("supplier_a", sku, quantity=5)
    assert order["status"] == "PENDING"
    assert order["quantity"] == 5
    
    # Confirm stock was deducted
    post_order_stock = client.check_stock("supplier_a", sku).available_qty
    assert post_order_stock == initial_stock - 5
    
    # 2. Cancel order
    cancelled = client.cancel_order(order["order_id"])
    assert cancelled["status"] == "CANCELLED"
    
    # Confirm stock was restored
    restored_stock = client.check_stock("supplier_a", sku).available_qty
    assert restored_stock == initial_stock

