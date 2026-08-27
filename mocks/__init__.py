"""
mocks — Mock inventory database, supplier APIs, and logistics carriers.
"""

from mocks.inventory_db import (
    SKU_CATALOG,
    SKURecord,
    WAREHOUSE_STOCK,
    WarehouseStock,
    get_all_skus,
    get_critical_items,
    get_low_stock_items,
    get_sku,
    get_stock,
)
from mocks.suppliers import (
    MockSupplierAPI,
    SupplierCatalog,
    SupplierID,
    SupplierQuote,
    StockItem,
    get_all_supplier_apis,
    query_all_suppliers,
)
from mocks.logistics import (
    FreightQuoteRequest,
    FreightQuoteResponse,
    calculate_freight_quote,
)

__all__ = [
    # Inventory DB
    "SKU_CATALOG",
    "SKURecord",
    "WAREHOUSE_STOCK",
    "WarehouseStock",
    "get_all_skus",
    "get_critical_items",
    "get_low_stock_items",
    "get_sku",
    "get_stock",
    # Suppliers
    "MockSupplierAPI",
    "SupplierCatalog",
    "SupplierID",
    "SupplierQuote",
    "StockItem",
    "get_all_supplier_apis",
    "query_all_suppliers",
    # Logistics
    "FreightQuoteRequest",
    "FreightQuoteResponse",
    "calculate_freight_quote",
]
