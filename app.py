import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

from core.orchestrator import orchestrator
from utils.data_loader import load_inventory_csv

app = FastAPI(title="AgentXcelerate Supply Chain API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class OptimizeRequest(BaseModel):
    order_id: Optional[str] = "ORD-0001"
    buyer_id: Optional[str] = "CUST-BUY-1001"
    part_id: str
    requested_qty: int
    max_lead_time_days: int
    priority: str
    special_instructions: Optional[str] = None

@app.post("/api/optimize")
async def optimize_order(request: OptimizeRequest):
    order_payload = {
        "order_id": request.order_id,
        "buyer_id": request.buyer_id,
        "part_id": request.part_id,
        "requested_qty": request.requested_qty,
        "max_lead_time_days": request.max_lead_time_days,
        "priority": request.priority.upper(),
        "special_instructions": request.special_instructions,
        "item": request.part_id,
        "quantity": request.requested_qty,
    }

    result = orchestrator.process_order(order_payload)
    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])
    return result

@app.get("/api/inventory")
async def get_inventory():
    inventory = load_inventory_csv()
    return {"inventory": inventory, "total_warehouses": len(inventory)}

frontend_dir = os.path.join(PROJECT_ROOT, "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    async def serve_original_frontend():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

    @app.get("/dashboard")
    async def serve_dashboard():
        dash_path = os.path.join(frontend_dir, "dashboard.html")
        target = dash_path if os.path.exists(dash_path) else os.path.join(frontend_dir, "index.html")
        return FileResponse(target)