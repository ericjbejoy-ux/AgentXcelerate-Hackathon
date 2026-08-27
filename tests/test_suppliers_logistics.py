"""
Tests for Supplier Mock APIs and Logistics Cost Estimator.
Run:  python -m pytest tests/test_suppliers_logistics.py -v
"""

from __future__ import annotations

import asyncio
import math

import pytest

from mocks.suppliers import (
    MockSupplierAPI,
    SupplierID,
    get_all_supplier_apis,
    query_all_suppliers,
)
from mocks.logistics import (
    LandedCostBreakdown,
    calculate_landed_cost,
    build_cost_breakdown,
    filter_by_lead_time,
    evaluate_suppliers,
)


# ── Supplier profile property tests ─────────────────────────────────────

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


# ── Catalog & quote tests ───────────────────────────────────────────────

class TestSupplierAPI:
    @pytest.mark.asyncio
    async def test_get_catalog_returns_items(self) -> None:
        api = MockSupplierAPI(SupplierID.A)
        catalog = await api.get_catalog()
        assert len(catalog.items) == 10
        assert catalog.supplier_id == "supplier_a"

    @pytest.mark.asyncio
    async def test_get_quote_known_sku(self) -> None:
        api = MockSupplierAPI(SupplierID.A)
        quote = await api.get_quote("SKU-MOTOR-001", quantity=5)
        assert quote is not None
        assert quote.sku == "SKU-MOTOR-001"
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
        qa = await a.get_quote("SKU-MOTOR-001")
        qb = await b.get_quote("SKU-MOTOR-001")
        assert qa is not None and qb is not None
        assert qb.unit_price > qa.unit_price  # Express is more expensive

    @pytest.mark.asyncio
    async def test_query_all_suppliers(self) -> None:
        quotes = await query_all_suppliers("SKU-VALVE-003", quantity=10)
        assert len(quotes) == 3
        supplier_ids = {q.supplier_id for q in quotes}
        assert supplier_ids == {"supplier_a", "supplier_b", "supplier_c"}


# ── Landed cost formula tests ───────────────────────────────────────────

class TestLandedCost:
    def test_formula_basic(self) -> None:
        # Landed Cost = (100 × 10) + 50 × e^(0.3)
        sub, freight, total = calculate_landed_cost(
            unit_price=100.0, quantity=10,
            freight_base_rate=50.0, speed_factor=0.3,
        )
        expected_sub = 1000.0
        expected_freight = round(50.0 * math.exp(0.3), 2)
        assert sub == expected_sub
        assert freight == expected_freight
        assert total == round(expected_sub + expected_freight, 2)

    def test_formula_high_speed_factor(self) -> None:
        _, freight, _ = calculate_landed_cost(
            unit_price=50.0, quantity=1,
            freight_base_rate=120.0, speed_factor=1.8,
        )
        expected = round(120.0 * math.exp(1.8), 2)
        assert freight == expected

    def test_zero_quantity(self) -> None:
        sub, freight, total = calculate_landed_cost(
            unit_price=100.0, quantity=0,
            freight_base_rate=50.0, speed_factor=0.5,
        )
        assert sub == 0.0
        assert total == freight  # only freight


# ── Constraint verifier tests ───────────────────────────────────────────

class TestConstraintVerifier:
    def _make_breakdown(
        self, supplier_id: str, cost: float, lead_time: float,
    ) -> LandedCostBreakdown:
        return LandedCostBreakdown(
            supplier_id=supplier_id,
            supplier_name=f"Supplier {supplier_id}",
            sku="SKU-TEST",
            quantity=1,
            unit_price=cost,
            item_subtotal=cost,
            freight_base_rate=0.0,
            speed_factor=0.0,
            freight_cost=0.0,
            total_landed_cost=cost,
            lead_time_days=lead_time,
            in_stock=True,
        )

    def test_all_viable(self) -> None:
        bds = [
            self._make_breakdown("a", 500, 3),
            self._make_breakdown("b", 300, 2),
        ]
        result = filter_by_lead_time(bds, max_lead_time_days=5.0)
        assert len(result.viable) == 2
        assert len(result.rejected) == 0
        assert result.cheapest is not None
        assert result.cheapest.supplier_id == "b"

    def test_partial_rejection(self) -> None:
        bds = [
            self._make_breakdown("a", 200, 10),
            self._make_breakdown("b", 600, 2),
        ]
        result = filter_by_lead_time(bds, max_lead_time_days=5.0)
        assert len(result.viable) == 1
        assert result.viable[0].supplier_id == "b"
        assert len(result.rejected) == 1
        assert result.rejected[0].supplier_id == "a"

    def test_all_rejected(self) -> None:
        bds = [
            self._make_breakdown("a", 200, 10),
            self._make_breakdown("c", 300, 8),
        ]
        result = filter_by_lead_time(bds, max_lead_time_days=1.0)
        assert len(result.viable) == 0
        assert result.cheapest is None
        assert result.fastest is None

    def test_fastest_picked_correctly(self) -> None:
        bds = [
            self._make_breakdown("a", 900, 4),
            self._make_breakdown("b", 300, 2),
            self._make_breakdown("c", 500, 3),
        ]
        result = filter_by_lead_time(bds, max_lead_time_days=5.0)
        assert result.fastest is not None
        assert result.fastest.supplier_id == "b"


# ── End-to-end integration test ─────────────────────────────────────────

class TestEvaluateSuppliers:
    @pytest.mark.asyncio
    async def test_full_pipeline(self) -> None:
        result = await evaluate_suppliers(
            sku="SKU-PUMP-004",
            quantity=5,
            max_lead_time_days=5.0,
        )
        # Supplier A (10 days) should be rejected; B (2d) and C (4d) viable
        rejected_ids = {r.supplier_id for r in result.rejected}
        viable_ids = {v.supplier_id for v in result.viable}
        assert "supplier_a" in rejected_ids
        assert "supplier_b" in viable_ids
        assert "supplier_c" in viable_ids
        assert result.cheapest is not None
        assert result.fastest is not None
        assert result.fastest.lead_time_days <= 5.0
