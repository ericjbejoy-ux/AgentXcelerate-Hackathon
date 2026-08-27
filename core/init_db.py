"""
SQLite Database Initialization
==============================
Loads CSV data into a SQLite database for fast querying.
Run once: python -m core.init_db
"""

import csv
import os
import sqlite3

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scm.db")


def init_database():
    """Create tables and load data from CSVs."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Drop existing tables
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    for row in c.fetchall():
        c.execute(f"DROP TABLE IF EXISTS {row[0]}")

    # ── Categories ──
    c.execute("""CREATE TABLE categories (
        category_id TEXT PRIMARY KEY,
        category_name TEXT
    )""")
    with open(os.path.join(DATA_DIR, "01_Categories.csv"), "r") as f:
        for row in csv.DictReader(f):
            c.execute("INSERT INTO categories VALUES (?, ?)", (row["Category_ID"], row["Category_Name"]))

    # ── Parts ──
    c.execute("""CREATE TABLE parts (
        part_id TEXT PRIMARY KEY,
        part_name TEXT,
        category_id TEXT,
        unit_price_usd REAL,
        FOREIGN KEY (category_id) REFERENCES categories(category_id)
    )""")
    with open(os.path.join(DATA_DIR, "02_Parts.csv"), "r") as f:
        for row in csv.DictReader(f):
            c.execute("INSERT INTO parts VALUES (?, ?, ?, ?)",
                      (row["Part_ID"], row["Part_Name"], row["Category_ID"], float(row["Unit_Price_USD"])))

    # ── Warehouses ──
    c.execute("""CREATE TABLE warehouses (
        warehouse_id TEXT PRIMARY KEY,
        warehouse_name TEXT,
        address TEXT,
        city TEXT,
        state TEXT,
        region TEXT,
        base_lead_days INTEGER,
        reliability REAL
    )""")
    with open(os.path.join(DATA_DIR, "04_Warehouses.csv"), "r") as f:
        for row in csv.DictReader(f):
            c.execute("INSERT INTO warehouses VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                      (row["Warehouse_ID"], row["Warehouse_Name"], row["Warehouse_Address"],
                       row["City"], row["State"], row["Region"],
                       int(row.get("Base_Lead_Days", 2)), float(row.get("Reliability", 0.95))))

    # ── Inventory ──
    c.execute("""CREATE TABLE inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        warehouse_id TEXT,
        part_id TEXT,
        on_hand INTEGER DEFAULT 0,
        reserved INTEGER DEFAULT 0,
        damaged INTEGER DEFAULT 0,
        available INTEGER DEFAULT 0,
        reorder_level INTEGER DEFAULT 10,
        FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id),
        FOREIGN KEY (part_id) REFERENCES parts(part_id)
    )""")
    c.execute("CREATE INDEX idx_inventory_sku ON inventory(part_id)")
    c.execute("CREATE INDEX idx_inventory_wh ON inventory(warehouse_id)")
    with open(os.path.join(DATA_DIR, "05_Inventory.csv"), "r") as f:
        for row in csv.DictReader(f):
            c.execute("INSERT INTO inventory (warehouse_id, part_id, on_hand, reserved, damaged, available, reorder_level) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (row["Warehouse_ID"], row["Part_ID"],
                       int(row.get("On_Hand", 0)), int(row.get("Reserved", 0)),
                       int(row.get("Damaged", 0)), int(row.get("Available", 0)),
                       int(row.get("Reorder_Level", 10))))

    # ── Part Demand (7-day) ──
    c.execute("""CREATE TABLE part_demand (
        part_id TEXT PRIMARY KEY,
        units_sold_7d INTEGER,
        units_returned_7d INTEGER,
        net_demand_7d INTEGER,
        FOREIGN KEY (part_id) REFERENCES parts(part_id)
    )""")
    with open(os.path.join(DATA_DIR, "03_Part_Demand_7D.csv"), "r") as f:
        for row in csv.DictReader(f):
            c.execute("INSERT OR REPLACE INTO part_demand VALUES (?, ?, ?, ?)",
                      (row.get("Part_ID", ""), int(row.get("Units_Sold_7_Days", 0)),
                       int(row.get("Units_Returned_7_Days", 0)),
                       int(row.get("Net_Units_Sold_7_Days", 0))))

    # ── Sales Transactions ──
    c.execute("""CREATE TABLE sales (
        sale_id TEXT PRIMARY KEY,
        timestamp TEXT,
        buyer_id TEXT,
        seller_id TEXT,
        warehouse_id TEXT,
        part_id TEXT,
        quantity_sold INTEGER,
        quantity_returned INTEGER,
        unit_price_usd REAL
    )""")
    c.execute("CREATE INDEX idx_sales_part ON sales(part_id)")
    c.execute("CREATE INDEX idx_sales_buyer ON sales(buyer_id)")
    c.execute("CREATE INDEX idx_sales_ts ON sales(timestamp)")
    with open(os.path.join(DATA_DIR, "10_Sales_Transactions.csv"), "r") as f:
        for row in csv.DictReader(f):
            c.execute("INSERT INTO sales VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                      (row["Sale_ID"], row["Timestamp"], row["Buyer_ID"],
                       row["Seller_ID"], row["Warehouse_ID"], row["Part_ID"],
                       int(row["Quantity_Sold"]), int(row["Quantity_Returned"]),
                       float(row["Unit_Price_USD"])))

    # ── Orders ──
    c.execute("""CREATE TABLE orders (
        order_id TEXT PRIMARY KEY,
        part_id TEXT,
        priority TEXT
    )""")
    with open(os.path.join(DATA_DIR, "06_Orders.csv"), "r") as f:
        for row in csv.DictReader(f):
            c.execute("INSERT INTO orders VALUES (?, ?, ?)",
                      (row["Order_ID"], row["Part_ID"], row["Priority"]))

    # ── Buyer Alternative Parts ──
    c.execute("""CREATE TABLE buyer_alternatives (
        buyer_id TEXT,
        requested_part_id TEXT,
        alternative_part_id TEXT
    )""")
    with open(os.path.join(DATA_DIR, "09_Buyer_Alternative_Parts.csv"), "r") as f:
        for row in csv.DictReader(f):
            c.execute("INSERT INTO buyer_alternatives VALUES (?, ?, ?)",
                      (row["Buyer_ID"], row["Requested_Part_ID"], row["Alternative_Part_ID"]))

    # ── Category Demand Time Series ──
    c.execute("""CREATE TABLE category_demand_ts (
        timestamp TEXT,
        category_id TEXT,
        daily_units_sold INTEGER,
        daily_units_returned INTEGER,
        net_units_sold INTEGER,
        rolling_7d_avg REAL
    )""")
    c.execute("CREATE INDEX idx_cdts_cat ON category_demand_ts(category_id)")
    with open(os.path.join(DATA_DIR, "13_Category_Demand_TimeSeries.csv"), "r") as f:
        for row in csv.DictReader(f):
            c.execute("INSERT INTO category_demand_ts VALUES (?, ?, ?, ?, ?, ?)",
                      (row["Timestamp"], row["Category_ID"],
                       int(row["Daily_Units_Sold"]), int(row["Daily_Units_Returned"]),
                       int(row["Net_Units_Sold"]), float(row["Rolling_7D_Avg_Net_Units"])))

    conn.commit()
    conn.close()
    print(f"Database created at {DB_PATH}")
    print(f"  Categories: 4")
    print(f"  Parts: 20")
    print(f"  Warehouses: 15")
    print(f"  Inventory: 300 rows")
    print(f"  Sales: 6000 rows")


if __name__ == "__main__":
    init_database()
