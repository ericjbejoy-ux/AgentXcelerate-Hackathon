from fastapi import FastAPI
from core.schemas import OrderRequest, StrategyRecommendation, FulfillmentOption

app = FastAPI(title="AgentXcelerate SCM Orchestrator")

@app.get("/")
def health_check():
    return {"status": "online", "system": "Autonomous SCM Multi-Agent Mesh"}

@app.post("/api/v1/process-order", response_model=StrategyRecommendation)
async def process_order(order: OrderRequest):
    dummy_option = FulfillmentOption(
        option_id="opt-01",
        strategy_name="Split Fulfillment (Re-allocate + Supplier Express)",
        source="Warehouse A (5 units) + Supplier B (15 units)",
        fulfilled_qty=order.requested_qty,
        unit_cost=120.0,
        total_cost=2400.0,
        lead_time_days=2,
        topsis_score=0.89
    )
    return StrategyRecommendation(
        order_id=order.order_id,
        selected_option=dummy_option,
        explanation="Re-allocated 5 units from low-priority stock and sourced 15 units from Supplier B to meet 2-day deadline.",
        alternative_options=[]
    )
