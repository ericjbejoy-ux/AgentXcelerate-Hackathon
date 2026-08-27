import json
import os

def load_inventory_candidates():
    path = os.path.join(os.path.dirname(__file__), "../mocks/inventory_db.json")
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)