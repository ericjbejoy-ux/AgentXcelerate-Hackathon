"""
Tests for Supplier Mock APIs and Logistics Cost Estimator.
Run:  python -m pytest tests/test_suppliers_logistics.py -v
"""

from __future__ import annotations

import pytest

from mocks.suppliers import (
    MockSupplierAPI,
    SupplierID,
    get_all_supplier_apis,
    query_all_suppliers,
)
from mocks.logistics import calculate_freight_quote


class TestSupplierProfiles:
    def test_supplier_a_properties(self) -> None:
        api = MockSupplierAPI(SupplierID.A)
        assert api.supplier_name == "Supplier A (Primary)"
        assert api.lead_time_days == 10.0
        assert api.speed_factor == 0.3

    def test_supplier_b_properties(self) -> None:
        api = MockSupplierAPI(SupplierID.B)
        assert api.supplier_name == "Supplier B (Express)"
        assert api.lead_time_days == 2.0
        assert api.speed_factor == 1.8

    def test_supplier_c_properties(self) -> None:
        api = MockSupplierAPI(SupplierID.C)
        assert api.supplier_name == "Supplier C (Alt Region)"
        assert api.lead_time_days == 4.0
        assert api.speed_factor == 1.0


class TestSupplierAPI:
    @pytest.mark.asyncio
    async def test_get_catalog_returns_items(self) -> None:
        api = MockSupplierAPI(SupplierID.A)
        catalog = await api.get_catalog()
        assert len(catalog.items) == 20
        assert catalog.supplier_id == "supplier_a"

    @pytest.mark.asyncio
    async def test_get_quote_known_sku(self) -> None:
        api = MockSupplierAPI(SupplierID.A)
        quote = await api.get_quote("HYD-1001", quantity=5)
        assert quote is not None
        assert quote.sku == "HYD-1001"
        assert quote.unit_price > 0

    @pytest.mark.asyncio
    async def test_get_quote_unknown_sku_returns_none(self) -> None:
        api = MockSupplierAPI(SupplierID.A)
        quote = await api.get_quote("SKU-NONEXISTENT-999")
        assert quote is None

    @pytest.mark.asyncio
    async def test_supplier_b_higher_prices_than_a(self) -> None:
        a = MockSupplierAPI(SupplierID.A)
        b = MockSupplierAPI(SupplierID.B)
        qa = await a.get_quote("HYD-1001")
        qb = await b.get_quote("HYD-1001")
        assert qa is not None and qb is not None
        assert qb.unit_price > qa.unit_price  # Express is more expensive

    @pytest.mark.asyncio
    async def test_query_all_suppliers(self) -> None:
        quotes = await query_all_suppliers("FIL-4001", quantity=10)
        assert len(quotes) == 3
        supplier_ids = {q.supplier_id for q in quotes}
        assert supplier_ids == {"supplier_a", "supplier_b", "supplier_c"}


class TestFreightLogisticsCalculations:
    def test_express_shipping_cost_and_transit(self) -> None:
        # Standard calculation with motor weight (12.5 kg * 5 units = 62.5 kg)
        result = calculate_freight_quote(
            origin="supplier_b",
            destination="ZONE-WEST",
            weight_kg=12.5,
            quantity=5,
            speed_mode="express",
            supplier_handling_days=2.0,
            base_freight_rate=120.0,
            speed_factor_val=1.8
        )
        assert result.transit_speed_mode == "EXPRESS"
        assert result.carrier_transit_days == 1.5
        assert result.total_transit_days == 3.5
        assert result.freight_cost > 0.0

    def test_standard_shipping_cost_and_transit(self) -> None:
        # Standard calculation with motor weight
        result = calculate_freight_quote(
            origin="supplier_a",
            destination="ZONE-EAST",
            weight_kg=12.5,
            quantity=5,
            speed_mode="standard",
            supplier_handling_days=10.0,
            base_freight_rate=50.0,
            speed_factor_val=0.3
        )
        assert result.transit_speed_mode == "STANDARD"
        assert result.carrier_transit_days == 4.0
        assert result.total_transit_days == 14.0
        assert result.freight_cost > 0.0
