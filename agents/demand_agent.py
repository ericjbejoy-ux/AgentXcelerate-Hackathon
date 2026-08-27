

def process_demand_layer(order: dict) -> dict:
    inventory_db = load_inventory_data() if "load_inventory_data" in globals() else []
    candidates = generate_candidate_options(order, inventory_db) if "generate_candidate_options" in globals() else []
    weights = calculate_priority_weights(order.get("priority", "MEDIUM")) if "calculate_priority_weights" in globals() else {}
    return {"order": order, "candidates": candidates, "weights": weights}
