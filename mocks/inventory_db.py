"""
Inventory Database
==================
Loads real spare parts logistics data from CSV files.
Indian warehouses, 20 parts across 4 categories, 300+ stock records.
"""

from __future__ import annotations

import csv
import os
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


class SKURecord(BaseModel):
    """Master definition of a stock-keeping unit."""
    sku: str
    description: str
    category: str
    base_unit_price: float = Field(ge=0, description="Reference price in USD")
    unit_of_measure: str = "EA"
    weight_kg: float = Field(default=1.0, ge=0, description="Per-unit weight for freight calc")
    critical: bool = Field(default=False, description="Is this a critical/safety part?")


class WarehouseStock(BaseModel):
    """Current stock snapshot in the warehouse distribution network."""
    sku: str
    on_hand_qty: int = Field(ge=0)
    reserved_qty: int = Field(ge=0)
    damaged_qty: int = Field(default=0, ge=0)
    reorder_point: int = Field(ge=0)
    max_capacity: int = Field(ge=0, default=200)
    warehouse_loc: str = Field(default="WH-CENTRAL")
    warehouse_address: str = ""
    warehouse_name: str = ""

    @property
    def available_qty(self) -> int:
        return max(0, self.on_hand_qty - self.reserved_qty - self.damaged_qty)

    @property
    def needs_reorder(self) -> bool:
        return self.available_qty <= self.reorder_point


class Warehouse(BaseModel):
    """Warehouse location with address and reliability data."""
    warehouse_id: str
    warehouse_name: str
    address: str
    city: str
    state: str
    region: str
    base_lead_days: int = 2
    reliability: float = 0.95


# ---------------------------------------------------------------------------
# CSV Loading Functions
# ---------------------------------------------------------------------------

def _load_csv(filename: str) -> List[dict]:
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def load_warehouses() -> Dict[str, Warehouse]:
    """Load warehouse data from CSV."""
    warehouses = {}
    for row in _load_csv("04_Warehouses.csv"):
        wh = Warehouse(
            warehouse_id=row["Warehouse_ID"],
            warehouse_name=row["Warehouse_Name"],
            address=row["Warehouse_Address"],
            city=row["City"],
            state=row["State"],
            region=row["Region"],
            base_lead_days=int(row.get("Base_Lead_Days", 2)),
            reliability=float(row.get("Reliability", 0.95)),
        )
        warehouses[wh.warehouse_id] = wh
    return warehouses


def load_parts() -> Dict[str, SKURecord]:
    """Load parts catalog from CSV."""
    parts = {}
    for row in _load_csv("02_Parts.csv"):
        sku = row["Part_ID"]
        parts[sku] = SKURecord(
            sku=sku,
            description=row["Part_Name"],
            category=row["Category_ID"],
            base_unit_price=float(row["Unit_Price_USD"]),
        )
    return parts


def load_inventory(warehouses: Dict[str, Warehouse]) -> Dict[str, List[WarehouseStock]]:
    """Load inventory from CSV, grouped by SKU."""
    inventory: Dict[str, List[WarehouseStock]] = {}
    for row in _load_csv("05_Inventory.csv"):
        sku = row["Part_ID"]
        wh_id = row["Warehouse_ID"]
        wh = warehouses.get(wh_id)

        stock = WarehouseStock(
            sku=sku,
            on_hand_qty=int(row.get("On_Hand", 0)),
            reserved_qty=int(row.get("Reserved", 0)),
            damaged_qty=int(row.get("Damaged", 0)),
            reorder_point=int(row.get("Reorder_Level", 10)),
            warehouse_loc=wh_id,
            warehouse_address=row.get("Warehouse_Address", wh.address if wh else ""),
            warehouse_name=wh.warehouse_name if wh else wh_id,
        )

        if sku not in inventory:
            inventory[sku] = []
        inventory[sku].append(stock)
    return inventory


def load_part_demand() -> Dict[str, dict]:
    """Load 7-day demand data from CSV."""
    demand = {}
    for row in _load_csv("03_Part_Demand_7D.csv"):
        sku = row.get("Part_ID", "")
        if sku:
            demand[sku] = {
                "units_sold_7d": int(row.get("Units_Sold_7_Days", 0)),
                "units_returned_7d": int(row.get("Units_Returned_7_Days", 0)),
                "net_demand_7d": int(row.get("Net_Units_Sold_7_Days", 0)),
            }
    return demand


# ---------------------------------------------------------------------------
# Initialize from CSV on import
# ---------------------------------------------------------------------------

WAREHOUSES: Dict[str, Warehouse] = load_warehouses()
SKU_CATALOG: Dict[str, SKURecord] = load_parts()
WAREHOUSE_STOCK: Dict[str, List[WarehouseStock]] = load_inventory(WAREHOUSES)
PART_DEMAND: Dict[str, dict] = load_part_demand()

# Legacy alias: map warehouse_id -> single stock record for backward compat
# (flattened: first warehouse per SKU)
FLAT_WAREHOUSE_STOCK: Dict[str, WarehouseStock] = {}
for sku, stocks in WAREHOUSE_STOCK.items():
    if stocks:
        FLAT_WAREHOUSE_STOCK[sku] = stocks[0]


# ---------------------------------------------------------------------------
# Query helpers (backward-compatible with existing code)
# ---------------------------------------------------------------------------

def get_all_skus() -> List[str]:
    return list(SKU_CATALOG.keys())


def get_sku(sku: str) -> Optional[SKURecord]:
    return SKU_CATALOG.get(sku)


def get_stock(sku: str) -> Optional[WarehouseStock]:
    """Get first warehouse stock record for backward compat."""
    return FLAT_WAREHOUSE_STOCK.get(sku)


def get_all_stocks(sku: str) -> List[WarehouseStock]:
    """Get all warehouse stock records for a SKU."""
    return WAREHOUSE_STOCK.get(sku, [])


def get_warehouse(warehouse_id: str) -> Optional[Warehouse]:
    return WAREHOUSES.get(warehouse_id)


def get_low_stock_items() -> List[WarehouseStock]:
    result = []
    for stocks in WAREHOUSE_STOCK.values():
        for s in stocks:
            if s.needs_reorder:
                result.append(s)
    return result


def get_critical_items() -> List[SKURecord]:
    return [r for r in SKU_CATALOG.values() if r.critical]


def get_parts_by_category(category: str) -> List[SKURecord]:
    return [r for r in SKU_CATALOG.values() if r.category.upper() == category.upper()]


def get_categories() -> List[str]:
    cats = set(r.category for r in SKU_CATALOG.values())
    return sorted(cats)


def get_demand(sku: str) -> Optional[dict]:
    return PART_DEMAND.get(sku)


def reserve_stock(sku: str, qty: int) -> bool:
    """Reserve stock from the first warehouse with enough available."""
    stocks = WAREHOUSE_STOCK.get(sku, [])
    for stock in stocks:
        if stock.available_qty >= qty:
            stock.reserved_qty += qty
            return True
    return False


def release_stock(sku: str, qty: int) -> bool:
    """Release reserved stock back to available."""
    stocks = WAREHOUSE_STOCK.get(sku, [])
    for stock in stocks:
        released = min(qty, stock.reserved_qty)
        if released > 0:
            stock.reserved_qty -= released
            qty -= released
            if qty <= 0:
                return True
    return qty <= 0
