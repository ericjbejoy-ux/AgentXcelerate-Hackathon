import uuid
import json
import logging
import asyncio
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")

import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

from core.schemas import OrderRequest, UnstructuredOrderRequest, ApprovalRequest
from core.orchestrator import orchestrator
from core.intent_router import intent_router
from core.event_bus import event_bus
from core.database import db

app = FastAPI(title="Autonomous SCM Multi-Agent Mesh")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health")
def health():
    return {"status": "online", "system": "Autonomous SCM"}


@app.get("/api/v1/inventory")
def get_inventory():
    catalog = db.inventory.get_catalog()
    inventory = []
    total_value = 0.0
    for sku, record in catalog.items():
        stocks = db.inventory.get_all_stocks(sku)
        total_on_hand = sum(s.on_hand_qty for s in stocks)
        total_reserved = sum(s.reserved_qty for s in stocks)
        total_available = sum(s.available_qty for s in stocks)
        needs_reorder = any(s.needs_reorder for s in stocks)
        wh_names = [s.warehouse_name for s in stocks if s.available_qty > 0]
        total_value += record.base_unit_price * total_on_hand
        inventory.append({
            "sku": sku,
            "description": record.description,
            "category": record.category,
            "warehouse_loc": wh_names[0] if wh_names else "N/A",
            "warehouses_available": len(stocks),
            "on_hand_qty": total_on_hand,
            "reserved_qty": total_reserved,
            "available_qty": total_available,
            "reorder_point": stocks[0].reorder_point if stocks else 0,
            "stock_pct": round((total_on_hand / 200) * 100, 1),
            "base_unit_price": record.base_unit_price,
            "is_critical": total_available < 10,
            "needs_reorder": needs_reorder,
        })
    low_stock = db.inventory.get_low_stock()
    critical = db.inventory.get_critical_parts()
    return {
        "inventory": inventory,
        "stats": {
            "total_skus": len(catalog),
            "low_stock_count": len(low_stock),
            "critical_parts_count": len(critical),
            "total_inventory_value_usd": round(total_value, 2),
        },
    }


@app.post("/api/v1/process-order")
@app.post("/process-order")
async def process_order(request: Request):
    try:
        body = await request.json()

        if "raw_text" in body and "part_id" not in body:
            order = await intent_router.parse_unstructured_order(
                raw_text=body["raw_text"],
                default_customer=body.get("customer_id"),
                override_priority=body.get("priority"),
            )
            order_dict = order.model_dump()
        else:
            order_req = OrderRequest(**body)
            order_dict = order_req.model_dump()

        result = orchestrator.process_order(order_dict, raw_text=body.get("raw_text"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/intent-parse")
async def intent_parse(request: UnstructuredOrderRequest):
    try:
        order = await intent_router.parse_unstructured_order(
            raw_text=request.raw_text,
            default_customer=request.customer_id,
            override_priority=request.override_priority,
        )
        return order.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/approve-execution")
def approve_execution(request: ApprovalRequest):
    try:
        result = orchestrator.approve_order(
            order_id=request.order_id,
            action=request.action,
            notes=request.notes or "",
        )
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/order/{order_id}")
def get_order(order_id: str):
    state = orchestrator.get_order(order_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    return {
        "order_id": state["order_id"],
        "status": state["status"],
        "approval_status": state["approval_status"],
        "trace_id": state["trace_id"],
        "selected_option": state["selected_option"],
        "explanation": state["explanation"],
    }


@app.get("/agent-status")
def agent_status():
    return orchestrator.get_agent_status()


@app.get("/orders")
def list_orders():
    return orchestrator.get_all_orders()


@app.get("/api/v1/analytics")
def get_analytics():
    raw_orders = orchestrator._orders
    orders_list = list(raw_orders.values())
    total = len(orders_list)
    executed = sum(1 for o in orders_list if o.get("status") == "EXECUTED")
    rejected = sum(1 for o in orders_list if o.get("status") == "REJECTED")
    pending = sum(1 for o in orders_list if o.get("status") == "PENDING_APPROVAL")

    # By priority
    by_priority = {}
    for o in orders_list:
        p = o.get("order_data", {}).get("priority", "Unknown")
        by_priority[p] = by_priority.get(p, 0) + 1

    # By part category
    catalog = db.inventory.get_catalog()
    by_category = {}
    for o in orders_list:
        part_id = o.get("order_data", {}).get("part_id", "")
        cat = "Unknown"
        for sku, rec in catalog.items():
            if sku == part_id:
                cat = rec.category
                break
        by_category[cat] = by_category.get(cat, 0) + 1

    # Cost and lead time from executed orders
    total_cost = 0
    total_lead = 0
    cost_count = 0
    for o in orders_list:
        sel = o.get("selected_option") or {}
        if sel and o.get("status") == "EXECUTED":
            tc = sel.get("total_cost", 0)
            lt = sel.get("lead_time_days", 0)
            if tc: total_cost += tc; cost_count += 1
            if lt: total_lead += lt

    # Recent orders (last 5)
    recent = sorted(orders_list, key=lambda x: x.get("created_at", ""), reverse=True)[:5]
    recent_summary = [
        {
            "order_id": r.get("order_id"),
            "status": r.get("status"),
            "approval_status": r.get("approval_status"),
            "part_id": r.get("order_data", {}).get("part_id"),
            "priority": r.get("order_data", {}).get("priority"),
            "created_at": r.get("created_at"),
        }
        for r in recent
    ]

    # Warehouse utilization
    inv = db.inventory.get_catalog()
    wh_usage = {}
    for sku, rec in inv.items():
        stocks = db.inventory.get_all_stocks(sku)
        for s in stocks:
            wh = s.warehouse_name
            if wh not in wh_usage:
                wh_usage[wh] = {"on_hand": 0, "reserved": 0, "available": 0}
            wh_usage[wh]["on_hand"] += s.on_hand_qty
            wh_usage[wh]["reserved"] += s.reserved_qty
            wh_usage[wh]["available"] += s.available_qty

    # Strategy breakdown
    by_strategy = {}
    for o in orders_list:
        sel = o.get("selected_option") or {}
        strat = sel.get("strategy_name", "Unknown")
        by_strategy[strat] = by_strategy.get(strat, 0) + 1

    return {
        "summary": {
            "total_orders": total,
            "executed": executed,
            "rejected": rejected,
            "pending": pending,
            "execution_rate": round(executed / total * 100, 1) if total else 0,
            "avg_cost": round(total_cost / cost_count, 2) if cost_count else 0,
            "avg_lead_time": round(total_lead / cost_count, 1) if cost_count else 0,
        },
        "by_priority": by_priority,
        "by_category": by_category,
        "by_strategy": by_strategy,
        "recent_orders": recent_summary,
        "warehouse_utilization": wh_usage,
    }


@app.get("/traces")
def list_traces():
    traces = event_bus.get_all_traces()
    return {"traces": traces, "count": len(traces)}


@app.get("/traces/{trace_id}/events")
def get_trace_events(trace_id: str):
    events = event_bus.get_events_by_trace(trace_id)
    return {"events": [e.model_dump() for e in events]}


@app.get("/api/v1/stream-events/{trace_id}")
async def stream_events(trace_id: str):
    """SSE endpoint — streams agent events as they happen for a given trace."""
    async def event_generator():
        sent_ids = set()
        max_wait = 30
        elapsed = 0
        while elapsed < max_wait:
            events = event_bus.get_events_by_trace(trace_id)
            for e in events:
                eid = e.event_id
                if eid not in sent_ids:
                    sent_ids.add(eid)
                    payload = json.dumps({
                        "event": e.event_type,
                        "agent": e.sender_agent,
                        "data": e.data,
                        "timestamp": e.timestamp.isoformat(),
                    })
                    yield f"data: {payload}\n\n"
            await asyncio.sleep(0.15)
            elapsed += 0.15
        yield f"data: {json.dumps({'event': 'STREAM_END', 'message': 'Done'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ── Frontend Serving ─────────────────────────────────────────
# Must be LAST — mount catches all non-API routes.

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")

if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
