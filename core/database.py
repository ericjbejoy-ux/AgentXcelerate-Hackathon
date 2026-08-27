"""
SQLite database layer for AgentXcelerate.
Stores all optimization requests and their results.
"""

import sqlite3
import json
import datetime
import os
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "supply_chain.db")

# ── Schema ────────────────────────────────────────────────────────────────────
_SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id        TEXT NOT NULL,
    buyer_id        TEXT,
    part_id         TEXT NOT NULL,
    requested_qty   INTEGER NOT NULL,
    priority        TEXT NOT NULL,
    max_lead_time   INTEGER,
    special_notes   TEXT,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS optimization_results (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id               TEXT NOT NULL,
    top_candidate_id       TEXT,
    top_warehouse_id       TEXT,
    topsis_score           REAL,
    total_cost             REAL,
    lead_time_days         INTEGER,
    fulfilled_by_date      TEXT,
    fulfillment_type       TEXT,
    approval_status        TEXT,
    net_margin             REAL,
    explanation            TEXT,
    agent_confidence       REAL,
    alternatives_json      TEXT,
    created_at             TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id  TEXT UNIQUE NOT NULL,
    email        TEXT UNIQUE NOT NULL,
    name         TEXT,
    company      TEXT,
    role         TEXT NOT NULL DEFAULT 'Buyer',
    created_at   TEXT NOT NULL
);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialise all tables (idempotent)."""
    with get_connection() as conn:
        conn.executescript(_SCHEMA)


def save_order(order_payload: dict) -> int:
    """Persist an incoming order. Returns the rowid."""
    now = datetime.datetime.utcnow().isoformat()
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO orders
               (order_id, buyer_id, part_id, requested_qty, priority,
                max_lead_time, special_notes, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                order_payload.get("order_id", ""),
                order_payload.get("buyer_id", ""),
                order_payload.get("part_id", order_payload.get("item", "")),
                order_payload.get("requested_qty", order_payload.get("quantity", 0)),
                order_payload.get("priority", "STANDARD"),
                order_payload.get("max_lead_time_days"),
                order_payload.get("special_instructions"),
                now,
            ),
        )
        return cur.lastrowid


def save_result(order_id: str, result: dict) -> int:
    """Persist a pipeline result. Returns the rowid."""
    now = datetime.datetime.utcnow().isoformat()
    ts  = result.get("top_strategy", {})
    si  = result.get("seller_impact", {})

    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO optimization_results
               (order_id, top_candidate_id, top_warehouse_id, topsis_score,
                total_cost, lead_time_days, fulfilled_by_date, fulfillment_type,
                approval_status, net_margin, explanation, agent_confidence,
                alternatives_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                order_id,
                ts.get("candidate_id"),
                ts.get("warehouse_id"),
                ts.get("topsis_score"),
                ts.get("total_cost"),
                ts.get("lead_time_days"),
                ts.get("fulfilled_by_date"),
                ts.get("fulfillment_type"),
                si.get("automated_approval_status"),
                si.get("net_margin"),
                result.get("explanation"),
                result.get("agent_confidence_score"),
                json.dumps(result.get("alternatives", [])),
                now,
            ),
        )
        return cur.lastrowid


def get_recent_results(limit: int = 20) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT r.*, o.part_id, o.requested_qty, o.priority, o.buyer_id
               FROM optimization_results r
               JOIN orders o ON r.order_id = o.order_id
               ORDER BY r.created_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]


def get_all_orders(limit: int = 50) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM orders ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(row) for row in rows]


# Auto-init on import
init_db()
