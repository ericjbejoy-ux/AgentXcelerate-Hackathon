# Mock Suppliers & Logistics Module

This package simulates external supplier REST APIs, manages central synthetic inventory catalogs, calculates dynamic logistics freight charges, and handles priority-based stock reallocations.

---

## Architecture & Data Flow

```
                     +---------------------------------------+
                     |           mocks/inventory_db.py       |
                     |     (SKU Catalog & Warehouse Stock)   |
                     +-----------------------+---------------+
                                             |
                                             v
                     +-----------------------+---------------+
                     |        mocks/supplier_server.py       |
                     |    (FastAPI Mock REST API on :8001)   |
                     +------------+--------------------+-----+
                                  |                    |
          (Seller Routes /seller) |                    | (Logistics Routes /logistics)
                                  v                    v
                     +------------+----------+   +-----+---------------+
                     |     Seller Endpoints  |   | Logistics Endpoints |
                     |   - Check stock logs  |   |  - Query transit    |
                     |   - Place/Cancel POs  |   |    speeds & weights |
                     |   - Reallocations     |   |  - Dynamic freight  |
                     +------------+----------+   +-----+---------------+
                                  |                    |
                                  +---------+----------+
                                            | (HTTP JSON)
                                            v
                     +----------------------+----------------+
                     |        mocks/supplier_client.py       |
                     |    (Python HTTP Wrapper for Agents)   |
                     +----------------------+----------------+
                                            |
                                            v
                     +----------------------+----------------+
                     |         Autonomous Orchestrator       |
                     |          (Fulfillment Agents)         |
                     +---------------------------------------+
```

---

## 1. Central Inventory: `inventory_db.py`
Shared database containing **10 synthetic SKUs** across categories (Connectivity, Actuators, Fluid Handling, Automation, etc.).
* **Model:** `SKURecord` (includes properties like `base_unit_price`, `weight_kg`, and a `critical` flag).
* **Model:** `WarehouseStock` (tracks `on_hand_qty`, `reserved_qty`, and the physical distribution center `warehouse_loc`).

---

## 2. API Server Endpoints: `supplier_server.py`
Starts a unified mock gateway on `http://localhost:8001`. Run using:
```bash
python -m mocks.supplier_server
```

### A. Seller & Order Management (`/seller/*`)
Used by agents to place purchase orders and by the frontend to monitor system state.

* **List Orders:** `GET /seller/orders` (or `?supplier_id=supplier_a`)
  * Returns the full log of incoming orders including allocation schemas, warehouse locations, gross margins, and operational directives.
* **Place Purchase Order:** `POST /seller/{supplier_id}/order`
  * **Payload:**
    ```json
    {
      "buyer_id": "CLIENT-NEXUS-9",
      "sku": "SKU-MOTOR-001",
      "quantity": 5,
      "priority": "HIGH",
      "destination_zone": "ZONE-EAST",
      "transit_speed_mode": "express"
    }
    ```
  * **Stock Reallocation Logic:** If a `HIGH` priority order has insufficient stock, the API automatically hijacks inventory from an active `LOW` or `MEDIUM` priority order, logging the hijacked target in `deprioritized_order_id` and applying a `10%` SLA penalty.
* **Cancel/Reject Order:** `POST /seller/orders/{order_id}/cancel`
  * Cancels the order, changes status to `CANCELLED`, and automatically restores the allocated stock back to the supplier's catalog.

### B. Logistics Carrier Simulator (`/logistics/*`)
Used by agents to calculate dynamic freight charges.

* **Retrieve Freight Quote:** `POST /logistics/quote`
  * **Payload:**
    ```json
    {
      "origin": "supplier_b",
      "destination": "ZONE-WEST",
      "sku": "SKU-MOTOR-001",
      "quantity": 5,
      "transit_speed_mode": "express"
    }
    ```
  * **Calculation Formula:**
    $$\text{Freight Cost} = \left(\text{Base Rate} + \text{Weight Markup}\right) \times e^{(\text{Speed Factor})} \times \text{Distance Factor}$$
  * Returns dynamic freight charges (adjusted for SKU weights) and transit days (carrier transit time + supplier handling delays).

---

## 3. Client SDK: `supplier_client.py`
Teammates can query the REST API directly using Python bindings:
```python
from mocks.supplier_client import SupplierClient

client = SupplierClient(base_url="http://localhost:8001")

# 1. Get Freight Rates & Speeds
shipping_quote = client.get_freight_quote(
    origin="supplier_b",
    destination="ZONE-WEST",
    sku="SKU-MOTOR-001",
    quantity=5,
    transit_speed_mode="express"
)
print(f"Transit: {shipping_quote.total_transit_days} days. Cost: ${shipping_quote.freight_cost}")

# 2. Place Order
order_receipt = client.place_seller_order(
    supplier_id="supplier_b",
    buyer_id="CLIENT-NEXUS-9",
    sku="SKU-MOTOR-001",
    quantity=5,
    priority="HIGH",
    destination_zone="ZONE-WEST",
    transit_speed_mode="express"
)
```

---

## 4. Supplier Dashboard: `supplier_dashboard.py`
Streamlit application visualizing live catalog levels, incoming orders, reallocations, and margin metrics. Runs on port `8502`:
```bash
streamlit run mocks/supplier_dashboard.py --server.port 8502
```
*Allows judges to manually cancel active orders to verify multi-agent fallback behavior.*
