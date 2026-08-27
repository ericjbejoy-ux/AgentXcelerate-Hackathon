

def generate_reasoning_with_groq(order: dict, optimal_option: dict) -> str:
    part_id = order.get("part_id", "Unknown Part")
    wh_id = optimal_option.get("warehouse_id", "Unknown Warehouse")
    score = optimal_option.get("topsis_score", 0.0)
    return f"Order for {part_id} optimized. Selected warehouse {wh_id} with TOPSIS score {score} based on cost, lead time, and reliability metrics."
