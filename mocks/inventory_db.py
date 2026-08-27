"""
Mock Inventory Database
========================
Centralized synthetic data source for the supply chain system.
Tracks warehouse locations, SKU weights, and inventory levels.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class SKURecord(BaseModel):
    """Master definition of a stock-keeping unit."""
    sku: str
    description: str
    category: str
    base_unit_price: float = Field(ge=0, description="Reference price in USD")
    unit_of_measure: str = "EA"
    weight_kg: float = Field(ge=0, description="Per-unit weight for freight calc")
    critical: bool = Field(default=False, description="Is this a critical/safety part?")


class WarehouseStock(BaseModel):
    """Current stock snapshot in the central warehouse distribution network."""
    sku: str
    on_hand_qty: int = Field(ge=0)
    reserved_qty: int = Field(ge=0)
    reorder_point: int = Field(ge=0)
    max_capacity: int = Field(ge=0)
    warehouse_loc: str = Field(default="WH-CENTRAL-01", description="Physical distribution center")

    @property
    def available_qty(self) -> int:
        return max(0, self.on_hand_qty - self.reserved_qty)

    @property
    def needs_reorder(self) -> bool:
        return self.available_qty <= self.reorder_point


# ---------------------------------------------------------------------------
# Synthetic SKU master data
# ---------------------------------------------------------------------------

SKU_CATALOG: Dict[str, SKURecord] = {
    "SKU-MOTOR-001": SKURecord(
        sku="SKU-MOTOR-001",
        description="Industrial servo motor 5kW",
        category="Actuators",
        base_unit_price=320.00,
        weight_kg=12.5,
        critical=True,
    ),
    "SKU-SENSOR-002": SKURecord(
        sku="SKU-SENSOR-002",
        description="IoT temperature sensor array",
        category="Sensors",
        base_unit_price=45.00,
        weight_kg=0.3,
        critical=False,
    ),
    "SKU-VALVE-003": SKURecord(
        sku="SKU-VALVE-003",
        description="Pneumatic control valve DN50",
        category="Flow Control",
        base_unit_price=185.00,
        weight_kg=4.2,
        critical=True,
    ),
    "SKU-PUMP-004": SKURecord(
        sku="SKU-PUMP-004",
        description="Centrifugal pump 10HP",
        category="Fluid Handling",
        base_unit_price=720.00,
        weight_kg=35.0,
        critical=True,
    ),
    "SKU-CABLE-005": SKURecord(
        sku="SKU-CABLE-005",
        description="Industrial Ethernet cable 100m spool",
        category="Connectivity",
        base_unit_price=28.00,
        weight_kg=5.8,
        critical=False,
    ),
    "SKU-BEARING-006": SKURecord(
        sku="SKU-BEARING-006",
        description="Deep groove ball bearing 6205",
        category="Mechanical",
        base_unit_price=18.50,
        weight_kg=0.15,
        critical=False,
    ),
    "SKU-PLC-007": SKURecord(
        sku="SKU-PLC-007",
        description="Compact PLC controller 16 I/O",
        category="Automation",
        base_unit_price=560.00,
        weight_kg=1.8,
        critical=True,
    ),
    "SKU-FILTER-008": SKURecord(
        sku="SKU-FILTER-008",
        description="Hydraulic return line filter 10μm",
        category="Filtration",
        base_unit_price=92.00,
        weight_kg=2.1,
        critical=False,
    ),
    "SKU-RELAY-009": SKURecord(
        sku="SKU-RELAY-009",
        description="Safety relay module 24VDC",
        category="Electrical",
        base_unit_price=135.00,
        weight_kg=0.4,
        critical=True,
    ),
    "SKU-GASKET-010": SKURecord(
        sku="SKU-GASKET-010",
        description="Spiral wound gasket DN100 SS316",
        category="Sealing",
        base_unit_price=42.00,
        weight_kg=0.6,
        critical=False,
    ),
}


# ---------------------------------------------------------------------------
# Synthetic warehouse stock levels
# ---------------------------------------------------------------------------

WAREHOUSE_STOCK: Dict[str, WarehouseStock] = {
    "SKU-MOTOR-001": WarehouseStock(
        sku="SKU-MOTOR-001", on_hand_qty=12, reserved_qty=4,
        reorder_point=5, max_capacity=50, warehouse_loc="WH-EAST-01",
    ),
    "SKU-SENSOR-002": WarehouseStock(
        sku="SKU-SENSOR-002", on_hand_qty=200, reserved_qty=30,
        reorder_point=50, max_capacity=500, warehouse_loc="WH-WEST-02",
    ),
    "SKU-VALVE-003": WarehouseStock(
        sku="SKU-VALVE-003", on_hand_qty=3, reserved_qty=2,
        reorder_point=10, max_capacity=80, warehouse_loc="WH-EAST-01",
    ),
    "SKU-PUMP-004": WarehouseStock(
        sku="SKU-PUMP-004", on_hand_qty=6, reserved_qty=1,
        reorder_point=3, max_capacity=20, warehouse_loc="WH-CENTRAL-01",
    ),
    "SKU-CABLE-005": WarehouseStock(
        sku="SKU-CABLE-005", on_hand_qty=85, reserved_qty=10,
        reorder_point=20, max_capacity=200, warehouse_loc="WH-WEST-02",
    ),
    "SKU-BEARING-006": WarehouseStock(
        sku="SKU-BEARING-006", on_hand_qty=450, reserved_qty=50,
        reorder_point=100, max_capacity=1000, warehouse_loc="WH-EAST-02",
    ),
    "SKU-PLC-007": WarehouseStock(
        sku="SKU-PLC-007", on_hand_qty=2, reserved_qty=2,
        reorder_point=3, max_capacity=15, warehouse_loc="WH-CENTRAL-01",
    ),
    "SKU-FILTER-008": WarehouseStock(
        sku="SKU-FILTER-008", on_hand_qty=35, reserved_qty=5,
        reorder_point=15, max_capacity=100, warehouse_loc="WH-EAST-01",
    ),
    "SKU-RELAY-009": WarehouseStock(
        sku="SKU-RELAY-009", on_hand_qty=18, reserved_qty=3,
        reorder_point=8, max_capacity=60, warehouse_loc="WH-CENTRAL-01",
    ),
    "SKU-GASKET-010": WarehouseStock(
        sku="SKU-GASKET-010", on_hand_qty=120, reserved_qty=0,
        reorder_point=30, max_capacity=300, warehouse_loc="WH-WEST-01",
    ),
}


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def get_all_skus() -> List[str]:
    return list(SKU_CATALOG.keys())


def get_sku(sku: str) -> Optional[SKURecord]:
    return SKU_CATALOG.get(sku)


def get_stock(sku: str) -> Optional[WarehouseStock]:
    return WAREHOUSE_STOCK.get(sku)


def get_low_stock_items() -> List[WarehouseStock]:
    return [s for s in WAREHOUSE_STOCK.values() if s.needs_reorder]


def get_critical_items() -> List[SKURecord]:
    return [r for r in SKU_CATALOG.values() if r.critical]
