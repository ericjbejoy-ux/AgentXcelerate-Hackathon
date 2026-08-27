"""
Mock data interfaces — re-exported from core.database for backward compatibility.
"""

from core.database import db

# Re-export for backward compatibility
from core.database import SKURecord, WarehouseStock, Warehouse

# Convenience re-exports
SKU_CATALOG = db.inventory.get_catalog()
WAREHOUSE_STOCK = {}

def get_sku(sku):
    return db.inventory.get_sku(sku)

def get_stock(sku):
    return db.inventory.get_stock(sku)

def get_all_skus():
    return db.inventory.get_all_skus()

def get_low_stock_items():
    return db.inventory.get_low_stock()

def get_critical_items():
    return [db.inventory.get_sku(s) for s in db.inventory.get_critical_parts()]

# Supplier re-exports
from mocks.suppliers import (
    MockSupplierAPI,
    SupplierCatalog,
    SupplierID,
    SupplierQuote,
    StockItem,
    get_all_supplier_apis,
    query_all_suppliers,
)

# Logistics re-exports
from mocks.logistics import (
    FreightQuoteRequest,
    FreightQuoteResponse,
    calculate_freight_quote,
)

__all__ = [
    "db",
    "SKU_CATALOG",
    "SKURecord",
    "WAREHOUSE_STOCK",
    "WarehouseStock",
    "get_all_skus",
    "get_critical_items",
    "get_low_stock_items",
    "get_sku",
    "get_stock",
    "MockSupplierAPI",
    "SupplierCatalog",
    "SupplierID",
    "SupplierQuote",
    "StockItem",
    "get_all_supplier_apis",
    "query_all_suppliers",
    "FreightQuoteRequest",
    "FreightQuoteResponse",
    "calculate_freight_quote",
]
