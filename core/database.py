"""
Unified Database Interface
==========================
SQLite-backed data access for all agents and endpoints.
Single import: from core.database import db
"""

from __future__ import annotations

import logging
import os
import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

logger = logging.getLogger("database")

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scm.db")


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# ── SKURecord / WarehouseStock as lightweight dataclasses ──

from dataclasses import dataclass


@dataclass
class SKURecord:
    sku: str
    description: str
    category: str
    base_unit_price: float
    weight_kg: float = 1.0

    @property
    def critical(self) -> bool:
        return False


@dataclass
class WarehouseStock:
    sku: str
    on_hand_qty: int
    reserved_qty: int
    damaged_qty: int
    reorder_point: int
    warehouse_loc: str
    warehouse_name: str = ""

    @property
    def available_qty(self) -> int:
        return max(0, self.on_hand_qty - self.reserved_qty - self.damaged_qty)

    @property
    def needs_reorder(self) -> bool:
        return self.available_qty <= self.reorder_point


@dataclass
class Warehouse:
    warehouse_id: str
    warehouse_name: str
    address: str
    city: str
    state: str
    region: str
    base_lead_days: int
    reliability: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None


# ── Inventory DB ──

class InventoryDB:

    def get_sku(self, sku: str) -> Optional[SKURecord]:
        with get_conn() as conn:
            row = conn.execute("SELECT * FROM parts WHERE part_id=?", (sku,)).fetchone()
            if row:
                # Estimate weight from category (kg per unit)
                cat_weights = {
                    "HYDRAULICS": 5.0, "ELECTRONIC": 1.0,
                    "FASTENERS": 0.5, "FILTERS": 1.5,
                }
                w = cat_weights.get(row["category_id"], 1.0)
                return SKURecord(row["part_id"], row["part_name"], row["category_id"],
                                 row["unit_price_usd"], w)
        return None

    def get_stock(self, sku: str) -> Optional[WarehouseStock]:
        with get_conn() as conn:
            row = conn.execute(
                "SELECT i.*, w.warehouse_name FROM inventory i "
                "JOIN warehouses w ON i.warehouse_id=w.warehouse_id "
                "WHERE i.part_id=? ORDER BY i.available DESC LIMIT 1", (sku,)
            ).fetchone()
            if row:
                return WarehouseStock(
                    sku=row["part_id"], on_hand_qty=row["on_hand"],
                    reserved_qty=row["reserved"], damaged_qty=row["damaged"],
                    reorder_point=row["reorder_level"], warehouse_loc=row["warehouse_id"],
                    warehouse_name=row["warehouse_name"],
                )
        return None

    def get_all_stocks(self, sku: str) -> List[WarehouseStock]:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT i.*, w.warehouse_name FROM inventory i "
                "JOIN warehouses w ON i.warehouse_id=w.warehouse_id "
                "WHERE i.part_id=? AND i.available>0 ORDER BY i.available DESC", (sku,)
            ).fetchall()
            return [WarehouseStock(
                sku=r["part_id"], on_hand_qty=r["on_hand"],
                reserved_qty=r["reserved"], damaged_qty=r["damaged"],
                reorder_point=r["reorder_level"], warehouse_loc=r["warehouse_id"],
                warehouse_name=r["warehouse_name"],
            ) for r in rows]

    def get_warehouse(self, warehouse_id: str) -> Optional[Warehouse]:
        with get_conn() as conn:
            row = conn.execute("SELECT * FROM warehouses WHERE warehouse_id=?", (warehouse_id,)).fetchone()
            if row:
                from core.geocoder import geocode
                coords = geocode(row["city"])
                return Warehouse(row["warehouse_id"], row["warehouse_name"], row["address"],
                                 row["city"], row["state"], row["region"],
                                 row["base_lead_days"], row["reliability"],
                                 latitude=coords[0] if coords else None,
                                 longitude=coords[1] if coords else None)
        return None

    def get_warehouses(self) -> Dict[str, Warehouse]:
        with get_conn() as conn:
            rows = conn.execute("SELECT * FROM warehouses").fetchall()
            from core.geocoder import geocode
            result = {}
            for r in rows:
                coords = geocode(r["city"])
                result[r["warehouse_id"]] = Warehouse(
                    r["warehouse_id"], r["warehouse_name"],
                    r["address"], r["city"], r["state"], r["region"],
                    r["base_lead_days"], r["reliability"],
                    latitude=coords[0] if coords else None,
                    longitude=coords[1] if coords else None)
            return result

    def get_all_skus(self) -> List[str]:
        with get_conn() as conn:
            return [r["part_id"] for r in conn.execute("SELECT part_id FROM parts").fetchall()]

    def get_categories(self) -> List[str]:
        with get_conn() as conn:
            return [r["category_id"] for r in conn.execute("SELECT category_id FROM categories").fetchall()]

    def get_parts_by_category(self, category: str) -> List[SKURecord]:
        with get_conn() as conn:
            rows = conn.execute("SELECT * FROM parts WHERE category_id=?", (category.upper(),)).fetchall()
            return [SKURecord(r["part_id"], r["part_name"], r["category_id"], r["unit_price_usd"]) for r in rows]

    def get_catalog(self) -> Dict[str, SKURecord]:
        with get_conn() as conn:
            rows = conn.execute("SELECT * FROM parts").fetchall()
            return {r["part_id"]: SKURecord(r["part_id"], r["part_name"], r["category_id"], r["unit_price_usd"]) for r in rows}

    def get_low_stock(self) -> List[WarehouseStock]:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT i.*, w.warehouse_name FROM inventory i "
                "JOIN warehouses w ON i.warehouse_id=w.warehouse_id "
                "WHERE i.available <= i.reorder_level"
            ).fetchall()
            return [WarehouseStock(
                sku=r["part_id"], on_hand_qty=r["on_hand"],
                reserved_qty=r["reserved"], damaged_qty=r["damaged"],
                reorder_point=r["reorder_level"], warehouse_loc=r["warehouse_id"],
                warehouse_name=r["warehouse_name"],
            ) for r in rows]

    def get_critical_parts(self) -> List[str]:
        """Return part_ids that have very low stock across all warehouses."""
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT part_id, SUM(available) as total_available FROM inventory "
                "GROUP BY part_id HAVING total_available < 10"
            ).fetchall()
            return [r["part_id"] for r in rows]

    def get_demand(self, sku: str) -> Optional[dict]:
        with get_conn() as conn:
            row = conn.execute("SELECT * FROM part_demand WHERE part_id=?", (sku,)).fetchone()
            if row:
                return {"units_sold_7d": row["units_sold_7d"],
                        "units_returned_7d": row["units_returned_7d"],
                        "net_demand_7d": row["net_demand_7d"]}
        return None

    def reserve(self, sku: str, qty: int) -> bool:
        with get_conn() as conn:
            row = conn.execute(
                "SELECT id, available FROM inventory WHERE part_id=? AND available>=? "
                "ORDER BY available DESC LIMIT 1", (sku, qty)
            ).fetchone()
            if row:
                conn.execute("UPDATE inventory SET reserved=reserved+?, available=available-? WHERE id=?",
                             (qty, qty, row["id"]))
                conn.commit()
                return True
        return False

    def release(self, sku: str, qty: int) -> bool:
        with get_conn() as conn:
            row = conn.execute(
                "SELECT id, reserved FROM inventory WHERE part_id=? AND reserved>0 "
                "ORDER BY reserved DESC LIMIT 1", (sku,)
            ).fetchone()
            if row:
                released = min(qty, row["reserved"])
                conn.execute("UPDATE inventory SET reserved=reserved-?, available=available+? WHERE id=?",
                             (released, released, row["id"]))
                conn.commit()
                return True
        return False

    def get_sales_stats(self, sku: str, days: int = 30) -> dict:
        with get_conn() as conn:
            row = conn.execute(
                "SELECT SUM(quantity_sold) as sold, SUM(quantity_returned) as returned "
                "FROM sales WHERE part_id=? AND timestamp >= date('now', ?)",
                (sku, f"-{days} days")
            ).fetchone()
            return {"sold": row["sold"] or 0, "returned": row["returned"] or 0}

    def get_buyer_history(self, buyer_id: str, limit: int = 50) -> List[dict]:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM sales WHERE buyer_id=? ORDER BY timestamp DESC LIMIT ?",
                (buyer_id, limit)
            ).fetchall()
            return [dict(r) for r in rows]

    def execute_order(self, order_id: str, part_id: str, qty: int, warehouse_id: str) -> bool:
        """Deduct stock after order approval."""
        with get_conn() as conn:
            row = conn.execute(
                "SELECT id, available FROM inventory WHERE part_id=? AND warehouse_id=? AND available>=?",
                (part_id, warehouse_id, qty)
            ).fetchone()
            if row:
                conn.execute(
                    "UPDATE inventory SET on_hand=on_hand-?, available=available-? WHERE id=?",
                    (qty, qty, row["id"])
                )
                conn.commit()
                return True
        return False

    # ── Buyer Sales Summary ──

    def get_buyer_sales_summary(self, buyer_id: str = None, limit: int = 50) -> List[dict]:
        with get_conn() as conn:
            if buyer_id:
                rows = conn.execute(
                    "SELECT * FROM buyer_sales_summary WHERE buyer_id=? ORDER BY last_purchase_timestamp DESC LIMIT ?",
                    (buyer_id, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM buyer_sales_summary ORDER BY last_purchase_timestamp DESC LIMIT ?",
                    (limit,)
                ).fetchall()
            return [dict(r) for r in rows]

    def get_buyer_top_parts(self, buyer_id: str, limit: int = 10) -> List[dict]:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM buyer_sales_summary WHERE buyer_id=? ORDER BY buyer_units_purchased DESC LIMIT ?",
                (buyer_id, limit)
            ).fetchall()
            return [dict(r) for r in rows]

    # ── Seller Sales Summary ──

    def get_seller_sales_summary(self, seller_id: str = None, warehouse_id: str = None, limit: int = 50) -> List[dict]:
        with get_conn() as conn:
            if seller_id:
                rows = conn.execute(
                    "SELECT * FROM seller_sales_summary WHERE seller_id=? ORDER BY last_sale_timestamp DESC LIMIT ?",
                    (seller_id, limit)
                ).fetchall()
            elif warehouse_id:
                rows = conn.execute(
                    "SELECT * FROM seller_sales_summary WHERE warehouse_id=? ORDER BY last_sale_timestamp DESC LIMIT ?",
                    (warehouse_id, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM seller_sales_summary ORDER BY last_sale_timestamp DESC LIMIT ?",
                    (limit,)
                ).fetchall()
            return [dict(r) for r in rows]

    # ── Demand Price History ──

    def get_demand_price_history(self, part_id: str = None, limit: int = 100) -> List[dict]:
        with get_conn() as conn:
            if part_id:
                rows = conn.execute(
                    "SELECT * FROM demand_price_history WHERE canonical_part_id=? ORDER BY date DESC LIMIT ?",
                    (part_id, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM demand_price_history ORDER BY date DESC LIMIT ?",
                    (limit,)
                ).fetchall()
            return [dict(r) for r in rows]

    # ── Macro Sentiment ──

    def get_macro_sentiment(self, limit: int = 50) -> List[dict]:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM macro_sentiment ORDER BY date DESC LIMIT ?",
                (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_latest_sentiment(self) -> Optional[dict]:
        with get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM macro_sentiment ORDER BY date DESC LIMIT 1"
            ).fetchone()
            return dict(row) if row else None

    # ── Marketing Calendar ──

    def get_marketing_calendar(self, limit: int = 50) -> List[dict]:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM marketing_calendar ORDER BY date DESC LIMIT ?",
                (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_active_promos(self) -> List[dict]:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM marketing_calendar WHERE promo_active=1 ORDER BY date DESC"
            ).fetchall()
            return [dict(r) for r in rows]


# ── Supplier DB ──

class SupplierDB:

    async def get_quote(self, sku: str, quantity: int = 1):
        from mocks.suppliers import query_all_suppliers
        return await query_all_suppliers(sku, quantity)

    def get_all_apis(self):
        from mocks.suppliers import get_all_supplier_apis
        return get_all_supplier_apis()


# ── Combined Database ──

class Database:
    def __init__(self):
        self.inventory = InventoryDB()
        self.suppliers = SupplierDB()

    def health(self) -> dict:
        with get_conn() as conn:
            parts = conn.execute("SELECT COUNT(*) as n FROM parts").fetchone()["n"]
            inv = conn.execute("SELECT COUNT(*) as n FROM inventory").fetchone()["n"]
            sales = conn.execute("SELECT COUNT(*) as n FROM sales").fetchone()["n"]
            return {"parts": parts, "inventory_rows": inv, "sales_rows": sales, "db_path": DB_PATH}


db = Database()
