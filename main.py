from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys

from agents.demand_agent import process_demand_layer
from utils.topsis import run_topsis_optimization
from agents.explanation_agent import generate_reasoning_with_groq

app = FastAPI(title="Autonomous SCM Multi-Agent Mesh")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class OrderRequest(BaseModel):
    order_id: str
    customer_id: str
    part_id: str
    requested_qty: int
    max_lead_time_days: int
    priority: str

@app.post("/api/v1/process-order")
def process_order(request: OrderRequest):
    try:
        order_dict = request.model_dump()
        
        # 1. Demand Execution
        demand_res = process_demand_layer(order_dict)
        
        # 2. Optimization Execution
        evaluated = run_topsis_optimization(demand_res["candidates"], demand_res["weights"])
        selected = evaluated[0]
        
        # 3. Groq LPU Reasoning
        explanation = generate_reasoning_with_groq(order_dict, selected, demand_res["weights"])
        
        return {
            "status": "success",
            "order_id": order_dict["order_id"],
            "selected_option": selected,
            "all_candidates": evaluated,
            "criteria_weights": demand_res["weights"],
            "explanation": explanation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))