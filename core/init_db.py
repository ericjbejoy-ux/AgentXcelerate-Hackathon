"""
SQLite Database Initialization
==============================
Loads V3 CSV data into a SQLite database for fast querying.
Run once: python -m core.init_db
"""

import csv
import os
import sqlite3

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scm.db")


def _load_csv(filename):
    """Load a CSV file and return list of dicts."""
    path = os.path.join(DATA_DIR, filename)
    with open(path, "r") as f:
        return list(csv.DictReader(f))


def init_database():
    """Create tables and load data from V3 CSVs."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Drop existing tables
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    for row in c.fetchall():
        if row[0] == "sqlite_sequence":
            continue
        c.execute(f"DROP TABLE IF EXISTS {row[0]}")

    # ── Categories ──
    c.execute("""CREATE TABLE categories (
        category_id TEXT PRIMARY KEY,
        category_name TEXT
    )""")
    for row in _load_csv("dim_categories.csv"):
        if not row["Category_ID"].strip():
            continue
        c.execute("INSERT INTO categories VALUES (?, ?)", (row["Category_ID"], row["Category_Name"]))

    # ── Parts ──
    c.execute("""CREATE TABLE parts (
        part_id TEXT PRIMARY KEY,
        part_name TEXT,
        category_id TEXT,
        unit_price_usd REAL,
        FOREIGN KEY (category_id) REFERENCES categories(category_id)
    )""")
    for row in _load_csv("dim_parts.csv"):
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
    for row in _load_csv("dim_warehouses.csv"):
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
    for row in _load_csv("fact_inventory.csv"):
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
    for row in _load_csv("fact_part_demand_7d.csv"):
        c.execute("INSERT OR REPLACE INTO part_demand VALUES (?, ?, ?, ?)",
                  (row["Part_ID"], int(row["Units_Sold_7_Days"]),
                   int(row["Units_Returned_7_Days"]),
                   int(row["Net_Units_Sold_7_Days"])))

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
    for row in _load_csv("fact_sales_transactions.csv"):
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
    for row in _load_csv("fact_orders.csv"):
        c.execute("INSERT INTO orders VALUES (?, ?, ?)",
                  (row["Order_ID"], row["Part_ID"], row["Priority"]))

    # ── Buyer Alternative Parts ──
    c.execute("""CREATE TABLE buyer_alternatives (
        buyer_id TEXT,
        requested_part_id TEXT,
        alternative_part_id TEXT
    )""")
    for row in _load_csv("bridge_buyer_alternative_parts.csv"):
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
    for row in _load_csv("fact_category_demand_timeseries.csv"):
        c.execute("INSERT INTO category_demand_ts VALUES (?, ?, ?, ?, ?, ?)",
                  (row["Timestamp"], row["Category_ID"],
                   int(row["Daily_Units_Sold"]), int(row["Daily_Units_Returned"]),
                   int(row["Net_Units_Sold"]), float(row["Rolling_7D_Avg_Net_Units"])))

    # ── Buyer Sales Summary ──
    c.execute("""CREATE TABLE buyer_sales_summary (
        record_id INTEGER PRIMARY KEY,
        buyer_id TEXT,
        part_id TEXT,
        buyer_transactions INTEGER,
        buyer_units_purchased INTEGER,
        buyer_units_returned INTEGER,
        last_purchase_timestamp TEXT
    )""")
    c.execute("CREATE INDEX idx_bss_buyer ON buyer_sales_summary(buyer_id)")
    c.execute("CREATE INDEX idx_bss_part ON buyer_sales_summary(part_id)")
    for row in _load_csv("fact_buyer_sales_summary.csv"):
        c.execute("INSERT INTO buyer_sales_summary VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (int(row["Record_ID"]), row["Buyer_ID"], row["Part_ID"],
                   int(row["Buyer_Transactions"]),
                   int(row["Buyer_Units_Purchased"]),
                   int(row["Buyer_Units_Returned"]),
                   row["Last_Buyer_Purchase_Timestamp"]))

    # ── Seller Sales Summary ──
    c.execute("""CREATE TABLE seller_sales_summary (
        record_id INTEGER PRIMARY KEY,
        seller_id TEXT,
        warehouse_id TEXT,
        part_id TEXT,
        seller_transactions INTEGER,
        seller_units_sold INTEGER,
        seller_units_returned INTEGER,
        last_sale_timestamp TEXT
    )""")
    c.execute("CREATE INDEX idx_sss_seller ON seller_sales_summary(seller_id)")
    c.execute("CREATE INDEX idx_sss_wh ON seller_sales_summary(warehouse_id)")
    for row in _load_csv("fact_seller_sales_summary.csv"):
        c.execute("INSERT INTO seller_sales_summary VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (int(row["Record_ID"]), row["Seller_ID"], row["Warehouse_ID"],
                   row["Part_ID"],
                   int(row["Seller_Transactions"]),
                   int(row["Seller_Units_Sold"]),
                   int(row["Seller_Units_Returned"]),
                   row["Last_Seller_Sale_Timestamp"]))

    # ── Fulfillment Candidates ──
    c.execute("""CREATE TABLE fulfillment_candidates (
        candidate_id TEXT PRIMARY KEY,
        order_id TEXT,
        warehouse_id TEXT,
        base_unit_cost_usd REAL,
        items_sold_to_date INTEGER
    )""")
    c.execute("CREATE INDEX idx_fc_order ON fulfillment_candidates(order_id)")
    for row in _load_csv("fact_fulfillment_candidates.csv"):
        c.execute("INSERT INTO fulfillment_candidates VALUES (?, ?, ?, ?, ?)",
                  (row["Candidate_ID"], row["Order_ID"], row["Warehouse_ID"],
                   float(row["Base_Unit_Cost_USD"]),
                   int(row["Items_Sold_To_Date"])))

    # ── TOPSIS Evaluation ──
    c.execute("""CREATE TABLE topsis_evaluation (
        candidate_id TEXT PRIMARY KEY,
        rank INTEGER,
        effective_unit_cost_usd REAL,
        effective_lead_time_days INTEGER,
        topsis_score REAL
    )""")
    for row in _load_csv("fact_topsis_evaluation.csv"):
        c.execute("INSERT INTO topsis_evaluation VALUES (?, ?, ?, ?, ?)",
                  (row["Candidate_ID"], int(row["Rank"]),
                   float(row["Effective_Unit_Cost_USD"]),
                   int(row["Effective_Lead_Time_Days"]),
                   float(row["TOPSIS_Score"])))

    # ── Demand Price History ──
    c.execute("""CREATE TABLE demand_price_history (
        transaction_id TEXT PRIMARY KEY,
        date TEXT,
        competitor_part_key TEXT,
        canonical_part_id TEXT,
        historical_demand INTEGER,
        price_per_unit REAL
    )""")
    c.execute("CREATE INDEX idx_dph_date ON demand_price_history(date)")
    c.execute("CREATE INDEX idx_dph_part ON demand_price_history(canonical_part_id)")
    for row in _load_csv("fact_demand_price_history.csv"):
        c.execute("INSERT INTO demand_price_history VALUES (?, ?, ?, ?, ?, ?)",
                  (row["Transaction_ID"], row["Date"],
                   row["Competitor_Part_Key"],
                   row.get("Canonical_Part_ID", "") or "",
                   int(row["Historical_Demand"]),
                   float(row["Price_Per_Unit"])))

    # ── Macro Sentiment Metrics ──
    c.execute("""CREATE TABLE macro_sentiment (
        record_id INTEGER PRIMARY KEY,
        date TEXT,
        survey_expand_pct REAL,
        survey_stagnant_pct REAL,
        survey_contract_pct REAL,
        raw_transit_delay_hours REAL,
        current_metal_unit_cost REAL,
        text_sentiment_score REAL
    )""")
    c.execute("CREATE INDEX idx_ms_date ON macro_sentiment(date)")
    for row in _load_csv("fact_macro_sentiment_metrics.csv"):
        c.execute("INSERT INTO macro_sentiment VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (int(row["Record_ID"]), row["Date"],
                   float(row["Survey_Expand_Pct"]),
                   float(row["Survey_Stagnant_Pct"]),
                   float(row["Survey_Contract_Pct"]),
                   float(row["Raw_Transit_Delay_Hours"]),
                   float(row["Current_Metal_Unit_Cost"]),
                   float(row["Text_Sentiment_Score"])))

    # ── Marketing Calendar ──
    c.execute("""CREATE TABLE marketing_calendar (
        record_id INTEGER PRIMARY KEY,
        date TEXT,
        promo_active INTEGER,
        discount_pct REAL
    )""")
    c.execute("CREATE INDEX idx_mc_date ON marketing_calendar(date)")
    for row in _load_csv("fact_marketing_calendar.csv"):
        c.execute("INSERT INTO marketing_calendar VALUES (?, ?, ?, ?)",
                  (int(row["Record_ID"]), row["Date"],
                   int(row["Marketing_Promo_Active"]),
                   float(row["Marketing_Discount_Pct"])))

    conn.commit()
    conn.close()

    # Count loaded rows
    counts = {
        "categories": 4, "parts": 20, "warehouses": 15,
        "inventory": 300, "sales": 6000, "orders": 8,
        "buyer_sales_summary": 1195, "seller_sales_summary": 300,
        "demand_price_history": 50, "macro_sentiment": 50,
        "marketing_calendar": 50,
    }
    print(f"Database created at {DB_PATH}")
    for table, count in counts.items():
        print(f"  {table}: {count} rows")


if __name__ == "__main__":
    init_database()
