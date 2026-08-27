
from utils.data_loader import load_inventory_candidates

def evaluate_logistics() -> list:
    candidates = load_inventory_candidates()
    for item in candidates:
        item["freight_surcharge"] = round(item.get("distance_km", 100) * 0.05, 2)
    return candidates

