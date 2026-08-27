
import os
import csv

def load_inventory_csv() -> list:
    # Returns default candidate list for optimization
    return [
        {
            "candidate_id": "WH-001",
            "warehouse_id": "WH-ALPHA",
            "warehouse_loc": "Chicago, IL",
            "item_sku": "ELE-RLY-133",
            "available_stock": 1500,
            "current_stock": 1500,
            "allocated_stock": 200,
            "remaining_stock": 1300,
            "unit_cost": 45.0,
            "lead_time_days": 2,
            "reliability_score": 0.95,
            "distance": 120
        },
        {
            "candidate_id": "WH-002",
            "warehouse_id": "WH-BETA",
            "warehouse_loc": "Dallas, TX",
            "item_sku": "ELE-RLY-133",
            "available_stock": 800,
            "current_stock": 800,
            "allocated_stock": 100,
            "remaining_stock": 700,
            "unit_cost": 42.0,
            "lead_time_days": 4,
            "reliability_score": 0.88,
            "distance": 450
        },
        {
            "candidate_id": "WH-003",
            "warehouse_id": "WH-GAMMA",
            "warehouse_loc": "Seattle, WA",
            "item_sku": "ELE-RLY-133",
            "available_stock": 2000,
            "current_stock": 2000,
            "allocated_stock": 500,
            "remaining_stock": 1500,
            "unit_cost": 48.0,
            "lead_time_days": 1,
            "reliability_score": 0.98,
            "distance": 80
        }
    ]

def load_suppliers_csv() -> list:
    return [
        {"supplier_id": "SUP-101", "name": "Global Tech Corp", "rating": 4.8},
        {"supplier_id": "SUP-102", "name": "Apex Logistics", "rating": 4.5}
    ]

