import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
from fastapi.testclient import TestClient

from main import app

from core.schemas import OrderRequest, UnstructuredOrderRequest, ApprovalRequest, AgentEvent
from core.intent_router import intent_router, _heuristic_fallback_parser
from core.orchestrator import orchestrator
from core.topsis_solver import calculate_topsis
import numpy as np



client = TestClient(app)


def test_health_endpoint():
    """Verify root health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "Autonomous SCM" in data["system"]


def test_intent_router_heuristic_fallback():
    """Test rule-based fallback parser for unstructured customer emails."""
    raw_email = "URGENT: We need 50 units of PART-X100 for Tesla within 3 days. Priority is Critical!"
    parsed = _heuristic_fallback_parser(raw_email)
    
    assert parsed["requested_qty"] == 50
    assert "PART-X100" in parsed["part_id"]
    assert parsed["max_lead_time_days"] == 3
    assert parsed["priority"] == "CRITICAL"
    assert "Tesla" in parsed["customer_id"]


def test_intent_parse_endpoint():
    """Verify POST /intent-parse endpoint."""
    payload = {
        "raw_text": "Hey team, please supply 25 pcs of PART-A102 to Boeing within 5 days. High priority.",
        "customer_id": "Boeing"
    }
    response = client.post("/intent-parse", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["customer_id"] == "Boeing"
    assert data["requested_qty"] == 25
    assert data["part_id"] == "PART-A102"
    assert data["max_lead_time_days"] == 5
    assert data["priority"] in ["HIGH", "CRITICAL"]


def test_topsis_solver_robustness():
    """Verify TOPSIS solver with multi-objective criteria and edge cases."""
    # Matrix: [Lead Time (min), Total Cost (min), Reliability (max)]
    matrix = np.array([
        [1.0, 450.0, 0.95],   # Fast, cheap, high reliability
        [5.0, 1200.0, 0.90],  # Slow, expensive
        [2.0, 800.0, 0.98]    # Fast, moderate cost
    ])
    weights = np.array([0.5, 0.3, 0.2])
    impacts = np.array([-1, -1, 1])
    
    scores = calculate_topsis(matrix, weights, impacts)
    assert len(scores) == 3
    # Option 1 should score highest
    assert scores[0] > scores[1]
    
    # Edge case: 1 row matrix
    single_score = calculate_topsis(np.array([[2.0, 500.0, 0.95]]), weights, impacts)
    assert len(single_score) == 1
    assert single_score[0] == 1.0


def test_process_order_structured():
    """Test full execution for structured OrderRequest."""
    payload = {
        "order_id": "ORD-TEST-001",
        "customer_id": "Acme Industrial",
        "part_id": "HYD-1001",
        "requested_qty": 5,
        "max_lead_time_days": 5,
        "priority": "HIGH"
    }
    response = client.post("/process-order", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["order_id"] == "ORD-TEST-001"
    assert data["status"] == "success"
    assert data["order_status"] == "PENDING_APPROVAL"
    assert data["selected_option"] is not None
    assert data["selected_option"]["total_cost"] > 0
    assert len(data["agent_events"]) > 0
    
    # Verify events follow AgentEvent schema
    for evt in data["agent_events"]:
        assert "trace_id" in evt
        assert "sender_agent" in evt
        assert "event_type" in evt
        assert "timestamp" in evt


def test_process_order_unstructured_text():
    """Test full LangGraph execution for unstructured raw email text."""
    payload = {
        "raw_text": "Need 15 units of MOTOR-V6 delivered to Ford within 4 days. Critical priority."
    }
    response = client.post("/process-order", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["order_status"] == "PENDING_APPROVAL"
    assert data["selected_option"]["fulfilled_qty"] == 15
    assert data["explanation"] != ""


def test_hitl_approval_and_execution_flow():
    """Test Human-In-The-Loop approval gate and state transition."""
    # 1. Process order
    order_id = "ORD-HITL-999"
    payload = {
        "order_id": order_id,
        "customer_id": "Tesla Motors",
        "part_id": "ELE-2001",
        "requested_qty": 2,
        "max_lead_time_days": 10,
        "priority": "CRITICAL"
    }
    res = client.post("/process-order", json=payload)
    assert res.status_code == 200
    trace_id = res.json()["trace_id"]
    
    # 2. Approve execution
    approval_payload = {
        "order_id": order_id,
        "trace_id": trace_id,
        "action": "APPROVE",
        "notes": "Verified by SCM Lead"
    }
    app_res = client.post("/approve-execution", json=approval_payload)
    assert app_res.status_code == 200
    app_data = app_res.json()
    assert app_data["status"] in ("EXECUTED", "EXECUTION_FAILED")
    assert app_data["executed_option"] is not None
    
    # 3. Check order state lookup
    order_state_res = client.get(f"/order/{order_id}")
    assert order_state_res.status_code == 200
    state_data = order_state_res.json()
    assert state_data["status"] in ("EXECUTED", "EXECUTION_FAILED")
    assert state_data["approval_status"] == "APPROVED"


def test_hitl_rejection_flow():
    """Test operator rejection in Human-In-The-Loop gate."""
    order_id = "ORD-REJECT-001"
    payload = {
        "order_id": order_id,
        "customer_id": "BudgetCorp",
        "part_id": "FAS-3001",
        "requested_qty": 5,
        "max_lead_time_days": 10,
        "priority": "LOW"
    }
    client.post("/process-order", json=payload)
    
    approval_payload = {
        "order_id": order_id,
        "action": "REJECT",
        "notes": "Cost exceeds customer budget limit"
    }
    res = client.post("/approve-execution", json=approval_payload)
    assert res.status_code == 200
    assert res.json()["status"] == "REJECTED"


def test_agent_status_endpoint():
    """Verify /agent-status endpoint returns full sub-agent topology and metrics."""
    response = client.get("/agent-status")
    assert response.status_code == 200
    data = response.json()
    assert data["system_status"] == "OPERATIONAL"
    assert len(data["active_graph_nodes"]) >= 3
    assert "DemandAgent" in data["agents"]
    assert "RankingEngine" in data["agents"]
    assert "ExplanationAgent" in data["agents"]
    assert "Orchestrator" in data["agents"]
    assert data["agents"]["DemandAgent"]["status"] == "HEALTHY"


def test_missing_stock_edge_case():
    """Verify graceful handling when warehouse has 0 stock for unknown SKU."""
    payload = {
        "order_id": "ORD-UNKNOWN-SKU",
        "customer_id": "CustomTech",
        "part_id": "NON-EXISTENT-PART-999",
        "requested_qty": 40,
        "max_lead_time_days": 5,
        "priority": "MEDIUM"
    }
    response = client.post("/process-order", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["selected_option"] is not None
    # Sourced via emergency supplier fallback without crashing
    assert data["selected_option"]["fulfilled_qty"] == 40


def test_list_orders_and_traces():
    """Verify /orders and /traces observability endpoints."""
    orders_res = client.get("/orders")
    assert orders_res.status_code == 200
    assert isinstance(orders_res.json(), list)
    
    traces_res = client.get("/traces")
    assert traces_res.status_code == 200
    assert "traces" in traces_res.json()


if __name__ == "__main__":
    tests = [
        test_health_endpoint,
        test_intent_router_heuristic_fallback,
        test_intent_parse_endpoint,
        test_topsis_solver_robustness,
        test_process_order_structured,
        test_process_order_unstructured_text,
        test_hitl_approval_and_execution_flow,
        test_hitl_rejection_flow,
        test_agent_status_endpoint,
        test_missing_stock_edge_case,
        test_list_orders_and_traces,
    ]
    print(f"Running {len(tests)} test suites for Orchestration & State Machine...")
    for t in tests:
        t()
        print(f"  [PASS] {t.__name__}")
    print("\nALL ORCHESTRATION & STATE MACHINE TESTS PASSED SUCCESSFULLY!")

