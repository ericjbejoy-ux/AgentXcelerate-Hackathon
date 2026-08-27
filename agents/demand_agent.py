
def process_demand(order: dict) -> dict:
    priority = order.get("priority", "MEDIUM").upper()
    if priority == "HIGH":
        weights = {"cost": 0.2, "lead_time": 0.5, "reliability": 0.3}
    elif priority == "LOW":
        weights = {"cost": 0.6, "lead_time": 0.2, "reliability": 0.2}
    else:
        weights = {"cost": 0.33, "lead_time": 0.33, "reliability": 0.34}
    return {"order": order, "weights": weights}

