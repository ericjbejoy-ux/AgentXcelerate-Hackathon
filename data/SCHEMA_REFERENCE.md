# AutoSCM — Data Schema Reference

All data formats used by the app. Add new rows matching these exact column headers.

---

## 1. Categories

**File:** `data/01_Categories.csv`
**Loaded into:** SQLite `categories` table

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| Category_ID | TEXT PK | Uppercase ID | `HYDRAULICS` |
| Category_Name | TEXT | Display name | `Hydraulics` |

**Existing rows (4):** ELECTRONIC, FASTENERS, FILTERS, HYDRAULICS

---

## 2. Parts

**File:** `data/02_Parts.csv`
**Loaded into:** SQLite `parts` table

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| Part_ID | TEXT PK | Category prefix + 4-digit number | `HYD-1001` |
| Part_Name | TEXT | Human-readable name | `Hydraulic Pump` |
| Category_ID | TEXT FK | References Categories.Category_ID | `HYDRAULICS` |
| Unit_Price_USD | REAL | Base unit price in USD | `450.0` |

**Existing rows:** 20 parts (5 per category)

| Category | Prefix | Parts |
|----------|--------|-------|
| HYDRAULICS | HYD- | HYD-1001 to HYD-1005 |
| ELECTRONIC | ELE- | ELE-2001 to ELE-2005 |
| FASTENERS | FAS- | FAS-3001 to FAS-3005 |
| FILTERS | FIL- | FIL-4001 to FIL-4005 |

**To add a new part:** Pick a category prefix + next available number. Example: `HYD-1006`.

---

## 3. Part Demand (7-Day)

**File:** `data/03_Part_Demand_7D.csv`
**Loaded into:** SQLite `part_demand` table

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| Part_ID | TEXT PK | References Parts.Part_ID | `HYD-1001` |
| Units_Sold_7_Days | INTEGER | Total units sold in last 7 days | `24` |
| Units_Returned_7_Days | INTEGER | Total units returned in last 7 days | `3` |
| Net_Units_Sold_7_Days | INTEGER | sold - returned | `21` |

**One row per Part_ID.** Must match a Part_ID from `02_Parts.csv`.

---

## 4. Warehouses

**File:** `data/04_Warehouses.csv`
**Loaded into:** SQLite `warehouses` table

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| Warehouse_ID | TEXT PK | WH-{Region}-{Code} | `WH-Central-TX` |
| Warehouse_Name | TEXT | City + descriptive name | `Hyderabad Central Hub` |
| Warehouse_Address | TEXT | Full street address (quoted if commas) | `"Plot 12, HITEC City..."` |
| City | TEXT | City name | `Hyderabad` |
| State | TEXT | State/province | `Telangana` |
| Region | TEXT | Geographic region | `South` |
| Base_Lead_Days | INTEGER | Standard delivery lead time | `2` |
| Reliability | REAL | Fulfillment reliability score (0.0–1.0) | `0.96` |

**Regions used:** South, East, West, North, Southwest, SouthCentral, Rockies

**Existing rows:** 15 warehouses across Indian cities

---

## 5. Inventory

**File:** `data/05_Inventory.csv`
**Loaded into:** SQLite `inventory` table

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| Warehouse_ID | TEXT FK | References Warehouses.Warehouse_ID | `WH-Central-TX` |
| Warehouse_Address | TEXT | Same as Warehouses address | `"Plot 12, HITEC..."` |
| Part_ID | TEXT FK | References Parts.Part_ID | `HYD-1001` |
| On_Hand | INTEGER | Total units in stock | `46` |
| Reserved | INTEGER | Units reserved for orders | `4` |
| Damaged | INTEGER | Units damaged/unusable | `0` |
| Available | INTEGER | On_Hand - Reserved - Damaged | `42` |
| Reorder_Level | INTEGER | Minimum before reorder alert | `9` |

**Existing rows:** 300 (20 parts × 15 warehouses). One row per Warehouse+Part combination.

**To add inventory:** Add a row for each new part at each warehouse where it's stocked.

---

## 6. Orders (Seed Data)

**File:** `data/06_Orders.csv`
**Loaded into:** SQLite `orders` table

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| Order_ID | TEXT PK | `ORD-` + 4 digits | `ORD-8821` |
| Part_ID | TEXT FK | References Parts.Part_ID | `HYD-1001` |
| Priority | TEXT | `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL` | `HIGH` |

**Existing rows:** 8 seed orders. Runtime orders are created via API and stored in-memory only.

---

## 7. Sales Transactions

**File:** `data/10_Sales_Transactions.csv`
**Loaded into:** SQLite `sales` table

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| Sale_ID | TEXT PK | `SALE-` + 5 digits | `SALE-00001` |
| Timestamp | TEXT | `YYYY-MM-DD HH:MM:SS` | `2026-03-31 19:55:16` |
| Buyer_ID | TEXT | Customer ID | `CUST-102` |
| Seller_ID | TEXT | Warehouse/seller name | `Mumbai West Hub` |
| Warehouse_ID | TEXT FK | References Warehouses.Warehouse_ID | `WH-West-CA` |
| Warehouse_Address | TEXT | Full address | `"MIDC Andheri..."` |
| Part_ID | TEXT FK | References Parts.Part_ID | `FIL-4003` |
| Quantity_Sold | INTEGER | Units sold | `7` |
| Quantity_Returned | INTEGER | Units returned (0 if none) | `0` |
| Unit_Price_USD | REAL | Actual sale price per unit | `45.17` |

**Existing rows:** 6,000 transactions.

---

## 8. Buyer Alternatives

**File:** `data/09_Buyer_Alternative_Parts.csv`

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| Buyer_ID | TEXT | Customer ID | `CUST-101` |
| Requested_Part_ID | TEXT FK | Originally requested part | `HYD-1001` |
| Alternative_Part_ID | TEXT FK | Acceptable substitute | `HYD-1001B` |

---

## 9. Category Demand Time Series

**File:** `data/13_Category_Demand_TimeSeries.csv`

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| Timestamp | TEXT | Date only `YYYY-MM-DD` | `2025-09-01` |
| Category_ID | TEXT FK | References Categories.Category_ID | `ELECTRONIC` |
| Daily_Units_Sold | INTEGER | Units sold that day | `14` |
| Daily_Units_Returned | INTEGER | Units returned that day | `0` |
| Net_Units_Sold | INTEGER | sold - returned | `14` |
| Rolling_7D_Avg_Net_Units | REAL | 7-day rolling average | `14.0` |

---

## 10. Fulfillment Decisions

**File:** `data/14_Fulfillment_Decision.csv`

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| Order_ID | TEXT FK | References Orders.Order_ID | `ORD-8821` |
| Warehouse_ID | TEXT FK | References Warehouses.Warehouse_ID | `WH-West-CA` |
| Warehouse_Address | TEXT | Full address | `"MIDC Andheri..."` |
| Decision | TEXT | `APPROVED` or `REJECTED` | `APPROVED` |
| TOPSIS_Score | REAL | Final TOPSIS score | `0.9523` |

---

## 11. Buyer Sales Summary

**File:** `data/11_Buyer_Sales_Summary.csv`

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| Buyer_ID | TEXT | Customer ID | `CUST-101` |
| Part_ID | TEXT FK | References Parts.Part_ID | `ELE-2001` |
| Buyer_Transactions | INTEGER | Total transaction count | `7` |
| Buyer_Units_Purchased | INTEGER | Total units bought | `11` |
| Buyer_Units_Returned | INTEGER | Total units returned | `0` |
| Last_Buyer_Purchase_Timestamp | TEXT | Most recent purchase datetime | `2026-07-26 19:08:43` |

---

## 12. Seller Sales Summary

**File:** `data/12_Seller_Sales_Summary.csv`

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| Seller_ID | TEXT | Seller/warehouse name | `Ahmedabad Southwest Hub` |
| Warehouse_ID | TEXT FK | References Warehouses.Warehouse_ID | `WH-Southwest-AZ` |
| Warehouse_Address | TEXT | Full address | `"Sitapura..."` |
| Part_ID | TEXT FK | References Parts.Part_ID | `ELE-2001` |
| Seller_Transactions | INTEGER | Total transaction count | `13` |
| Seller_Units_Sold | INTEGER | Total units sold | `27` |
| Seller_Units_Returned | INTEGER | Total units returned | `0` |
| Last_Seller_Sale_Timestamp | TEXT | Most recent sale datetime | `2026-07-12 18:15:06` |

---

## 13. Candidates (Seed Evaluation)

**File:** `data/07_Candidates.csv`

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| Candidate_ID | TEXT PK | `OPT-` + 3 digits | `OPT-001` |
| Order_ID | TEXT FK | References Orders.Order_ID | `ORD-8821` |
| Warehouse_ID | TEXT FK | References Warehouses.Warehouse_ID | `WH-West-CA` |
| Warehouse_Address | TEXT | Full address | `"MIDC Andheri..."` |
| Base_Unit_Cost_USD | REAL | Unit cost before adjustments | `486.0` |
| Items_Sold_To_Date | INTEGER | Historical sales volume | `1075` |

---

## 14. TOPSIS Evaluation (Seed)

**File:** `data/08_TOPSIS_Evaluation.csv`

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| Candidate_ID | TEXT FK | References Candidates.Candidate_ID | `OPT-001` |
| Rank | INTEGER | Final ranking (1 = best) | `1` |
| Effective_Unit_Cost_USD | REAL | Adjusted unit cost | `486.0` |
| Effective_Lead_Time_Days | INTEGER | Adjusted lead time | `1` |
| TOPSIS_Score | REAL | Final score (0–1) | `0.9523` |

---

## 15. Frontend Part Catalog (Hardcoded)

**File:** `frontend/script.js` — `partCatalog` object

Must stay in sync with `02_Parts.csv`. Used for the dropdown UI.

```javascript
const partCatalog = {
  Hydraulics: [
    { name: "Hydraulic Pump",        id: "HYD-1001" },
    { name: "Hydraulic Cylinder",     id: "HYD-1002" },
    { name: "Hydraulic Hose",         id: "HYD-1003" },
    { name: "Hydraulic Valve",        id: "HYD-1004" },
    { name: "Pressure Relief Valve",  id: "HYD-1005" },
  ],
  Electronic: [
    { name: "Control Module",        id: "ELE-2001" },
    { name: "Electronic Sensor",     id: "ELE-2002" },
    { name: "Relay Module",          id: "ELE-2003" },
    { name: "Ignition Controller",   id: "ELE-2004" },
    { name: "Voltage Regulator",     id: "ELE-2005" },
  ],
  Fasteners: [
    { name: "Hex Bolt Set",          id: "FAS-3001" },
    { name: "Lock Nut Set",          id: "FAS-3002" },
    { name: "Mounting Screw Set",    id: "FAS-3003" },
    { name: "Threaded Rod",          id: "FAS-3004" },
    { name: "Retaining Ring Set",    id: "FAS-3005" },
  ],
  Filters: [
    { name: "Hydraulic Filter",      id: "FIL-4001" },
    { name: "Oil Filter",            id: "FIL-4002" },
    { name: "Air Filter",            id: "FIL-4003" },
    { name: "Fuel Filter",           id: "FIL-4004" },
    { name: "Return Line Filter",    id: "FIL-4005" },
  ],
};
```

---

## 16. Mock Supplier Profiles

**File:** `mocks/suppliers.py` — `_PROFILES` dict

| Field | Supplier A (Primary) | Supplier B (Express) | Supplier C (Alt Region) |
|-------|---------------------|---------------------|------------------------|
| lead_time_days | 10.0 | 2.0 | 4.0 |
| freight_base_rate | 50.0 | 120.0 | 80.0 |
| speed_factor | 0.3 | 1.8 | 1.0 |
| price_multiplier | 1.0 | 1.45 | 1.15 |
| stock_ratio | 1.0 | 0.35 | 0.60 |
| max_stock | 500 | 500 | 500 |

Supplier catalogs are auto-generated from `db.inventory.get_catalog()` × `price_multiplier` with random ±20 stock jitter.

---

## 17. Mock Logistics Distance Factors

**File:** `mocks/logistics.py` — `_DISTANCE_FACTORS` dict

| Origin | ZONE-EAST | ZONE-WEST | ZONE-CENTRAL |
|--------|-----------|-----------|-------------|
| supplier_a | 1.0 | 1.5 | 1.2 |
| supplier_b | 1.4 | 1.0 | 1.1 |
| supplier_c | 2.2 | 2.5 | 2.0 |

**Freight formula:** `(base_rate + weight_kg * quantity * 0.15) * exp(speed_factor) * distance_factor`

---

## 18. Demo Users (Frontend)

**File:** `frontend/script.js` — `demoUsers` array

```javascript
[
  { role: "Buyer",  name: "Arjun Mehta",   email: "buyer@demo.com",  password: "buyer123",  company: "Mumbai Industrial Corp",  customerId: "CUST-101" },
  { role: "Seller", name: "Priya Sharma",   email: "seller@demo.com", password: "seller123", company: "Hyderabad Parts Supply", customerId: "CUST-SELLER-001" },
]
```

---

## How to Add New Data

### Adding a new part:
1. Add row to `02_Parts.csv` with next available ID (e.g., `HYD-1006`)
2. Add row to `03_Part_Demand_7D.csv` for the new Part_ID
3. Add inventory rows to `05_Inventory.csv` — one per warehouse where stocked
4. Add entry to `partCatalog` in `frontend/script.js` under the right category

### Adding a new warehouse:
1. Add row to `04_Warehouses.csv`
2. Add inventory rows to `05_Inventory.csv` for every part stocked there

### Adding a new category:
1. Add row to `01_Categories.csv`
2. Add parts to `02_Parts.csv` with that Category_ID
3. Add category to `partCatalog` in `frontend/script.js`
