# Mock Suppliers & Logistics Module

This package mock-simulates external supplier REST APIs, manages central synthetic inventory data, and calculates total landed logistics costs with lead-time constraints.

## Architecture & Data Flow

```
                     +---------------------------------------+
                     |           mocks/inventory_db.py       |
                     |  (SKU Master Catalog & Base Prices)   |
                     +-----------------------+---------------+
                                             |
                                             v
                     +---------------------------------------+
                     |           mocks/suppliers.py          |
                     |     (Supplier Profiles A, B, & C)     |
                     +-----------------------+---------------+
                                             |
                                             v
                     +---------------------------------------+
                     |        mocks/supplier_server.py       |
                     |    (FastAPI Mock REST API on :8001)   |
                     +-----------------------+---------------+
                                             | (HTTP requests)
                                             v
                     +---------------------------------------+
                     |        mocks/supplier_client.py       |
                     |    (Python HTTP Wrapper for Agents)   |
                     +-----------------------+---------------+
                                             |
                                             v
                     +---------------------------------------+
                     |           mocks/logistics.py          |
                     |   (Landed Costs & Constraint Filter)  |
                     +---------------------------------------+
```

---

## 1. Central Inventory: `inventory_db.py`
Acts as the shared single source of truth. Contains **10 synthetic SKUs** across categories (Connectivity, Actuators, Fluid Handling, Automation, etc.).
* **Model:** `SKURecord` (includes properties like `base_unit_price`, `weight_kg`, and a `critical` flag).
* **Model:** `WarehouseStock` (tracks `on_hand_qty`, `reserved_qty`, and triggers `needs_reorder`).

---

## 2. Supplier Profiles: `suppliers.py`
Defines 3 distinct vendor behaviors matching the hackathon criteria:
1. **Supplier A (Primary):** Full stock (1.0x ratio), base prices (1.0x multiplier), slow lead time (10 days), low speed factor (0.3).
2. **Supplier B (Express):** Partial stock (0.35x ratio), premium prices (1.45x markup), fast lead time (2 days), high speed factor (1.8).
3. **Supplier C (Alt Region):** Medium stock (0.60x ratio), mid prices (1.15x markup), medium lead time (4 days), variable speed factor (1.0).

---

## 3. REST API Server: `supplier_server.py`
Simulates external REST endpoints. Run it via:
```bash
python -m mocks.supplier_server
# Server starts on http://localhost:8001
```
### Primary Endpoints:
* `GET /health`: Returns loaded mock suppliers.
* `GET /{supplier_id}/catalog`: Fetches the supplier's stock catalog.
* `GET /{supplier_id}/quote?sku={sku}&quantity={q}`: Requests a price and lead-time quote.
* `GET /quotes/all?sku={sku}&quantity={q}`: Concurrently queries all 3 suppliers (fan-out pattern).

---

## 4. Client Wrapper: `supplier_client.py`
Teammates should import `SupplierClient` to query suppliers over HTTP:
```python
from mocks.supplier_client import SupplierClient

client = SupplierClient(base_url="http://localhost:8001")
# Get quotes from all 3 suppliers
quotes = client.get_all_quotes(sku="SKU-MOTOR-001", quantity=5)
```

---

## 5. Cost & Constraint Engine: `logistics.py`
Calculates final metrics and filters viable shipping paths.
* **Landed Cost Formula:**
  $$\text{Landed Cost} = (\text{Unit Price} \times Q) + \text{Freight Base Rate} \times e^{(\text{Speed Factor})}$$
* **Constraint Filtering:** Partition quotes into `viable` vs `rejected` categories matching the customer's maximum lead-time limit.

### Usage:
```python
from mocks.logistics import build_cost_breakdown, filter_by_lead_time

# 1. Calculate costs
breakdowns = [build_cost_breakdown(quote, quantity=5) for quote in quotes]

# 2. Filter by threshold (e.g., max 5 days)
result = filter_by_lead_time(breakdowns, max_lead_time_days=5.0)

print(result.cheapest) # Best price among matching paths
print(result.fastest)  # Shortest transit time among matching paths
```

---

## 🔄 Keeping this File Synced

To ensure this document does not drift from code changes, follow these guidelines:

1. **Verify Changes via Tests:**
   Run the tests before updating anything. If you alter the data models or mock structures, update the test suite to reflect those modifications:
   ```bash
   pytest tests/test_supplier_server.py
   pytest tests/test_suppliers_logistics.py
   ```
2. **Formula Alignment:**
   The landed cost formula in `logistics.py` (`calculate_landed_cost`) **must** mathematically match the equation documented in this file.
3. **Endpoint Contracts:**
   If you add/modify paths in `supplier_server.py`, immediately add the signature to Section 3 above and update `supplier_client.py` accordingly.
4. **Pydantic V2 Consistency:**
   Ensure any changes to the schemas in `inventory_db.py`, `suppliers.py`, or `logistics.py` use Pydantic V2 definitions and reflect any parameter type shifts here.
