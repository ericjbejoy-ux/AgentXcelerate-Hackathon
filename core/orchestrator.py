"""
Central Orchestrator Agent
==========================
Receives order requests, delegates to demand agent, runs TOPSIS, and manages state.
"""
from __future__ import annotations

import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from core.event_bus import event_bus, AgentEvent, create_event
from core.schemas import OrderRequest, StrategyRecommendation, FulfillmentOption
from core.topsis import run_topsis_optimization
from core.database import db
from agents.demand_agent import process_demand_layer
from agents.explanation_agent import generate_reasoning_with_groq

logger = logging.getLogger("orchestrator")


class Orchestrator:
    """
    Central orchestration agent for the SCM system.

    Workflow:
    1. Receive OrderRequest from frontend
    2. Delegate to demand_agent for candidate generation
    3. Run TOPSIS to rank candidates
    4. Generate explanation via explanation_agent
    5. Return StrategyRecommendation with state management
    """

    def __init__(self):
        self._orders: Dict[str, Dict[str, Any]] = {}

    def process_order(self, order_dict: dict, raw_text: Optional[str] = None) -> dict:
        trace_id = f"trace-{uuid.uuid4().hex[:8]}"
        order_id = order_dict.get("order_id") or f"ORD-{uuid.uuid4().hex[:6].upper()}"
        order_dict["order_id"] = order_id
        logger.info("[%s] Processing order %s for %s x %s", trace_id[:8], order_id, order_dict.get("requested_qty"), order_dict.get("part_id"))

        event_bus.publish_sync(create_event(
            sender_agent="Orchestrator",
            event_type="ORDER_RECEIVED",
            data={"order": order_dict, "message": f"Received order {order_id} for {order_dict.get('part_id')} x{order_dict.get('requested_qty')}"},
            trace_id=trace_id,
        ))

        event_bus.publish_sync(create_event(
            sender_agent="Orchestrator",
            event_type="AGENT_STATUS",
            data={"agent": "Orchestrator", "status": "working", "message": "Delegating to DemandAgent for candidate generation..."},
            trace_id=trace_id,
        ))

        demand_result = process_demand_layer(order_dict)
        wh_count = sum(1 for c in demand_result["candidates"] if c.get("warehouse_id"))
        sup_count = len(demand_result["candidates"]) - wh_count
        logger.info("[%s] Generated %d candidates (%d warehouse, %d supplier)", trace_id[:8], len(demand_result["candidates"]), wh_count, sup_count)

        event_bus.publish_sync(create_event(
            sender_agent="DemandAgent",
            event_type="CANDIDATES_GENERATED",
            data={
                "candidate_count": len(demand_result["candidates"]),
                "warehouse_count": wh_count,
                "supplier_count": sup_count,
                "message": f"Found {wh_count} warehouse + {sup_count} supplier options"
            },
            trace_id=trace_id,
        ))

        event_bus.publish_sync(create_event(
            sender_agent="DemandAgent",
            event_type="AGENT_STATUS",
            data={"agent": "DemandAgent", "status": "done", "message": f"Generated {len(demand_result['candidates'])} fulfillment candidates"},
            trace_id=trace_id,
        ))

        event_bus.publish_sync(create_event(
            sender_agent="Orchestrator",
            event_type="AGENT_STATUS",
            data={"agent": "Orchestrator", "status": "working", "message": "Running TOPSIS multi-criteria ranking..."},
            trace_id=trace_id,
        ))

        ranked = run_topsis_optimization(demand_result["candidates"], demand_result["weights"])
        if ranked:
            logger.info("[%s] TOPSIS ranked %d candidates, winner: %s (score=%.4f)", trace_id[:8], len(ranked), ranked[0]["strategy_name"], ranked[0]["topsis_score"])
        else:
            logger.warning("[%s] TOPSIS returned 0 candidates", trace_id[:8])

        # Enrich candidates with frontend-expected fields
        max_lead = order_dict.get("max_lead_time_days", 999)
        for i, c in enumerate(ranked):
            c["candidate_id"] = c.get("option_id", f"CANDIDATE-{i+1}")
            c["sku"] = order_dict.get("part_id", "")
            c["can_fulfill"] = c.get("fulfilled_qty", 0) >= order_dict.get("requested_qty", 0)
            c["available_stock"] = c.get("fulfilled_qty", 0)

        winner = ranked[0] if ranked else None
        event_bus.publish_sync(create_event(
            sender_agent="RankingEngine",
            event_type="TOPSIS_COMPLETED",
            data={
                "selected": winner,
                "total_ranked": len(ranked),
                "message": f"Winner: {winner['strategy_name']} (score={winner['topsis_score']:.4f})" if winner else "No candidates ranked"
            },
            trace_id=trace_id,
        ))

        event_bus.publish_sync(create_event(
            sender_agent="RankingEngine",
            event_type="AGENT_STATUS",
            data={"agent": "RankingEngine", "status": "done", "message": f"Ranked {len(ranked)} candidates via TOPSIS"},
            trace_id=trace_id,
        ))

        explanation = ""
        if ranked:
            event_bus.publish_sync(create_event(
                sender_agent="Orchestrator",
                event_type="AGENT_STATUS",
                data={"agent": "Orchestrator", "status": "working", "message": "Generating AI explanation via Groq LLM..."},
                trace_id=trace_id,
            ))
            logger.info("[%s] Generating LLM explanation...", trace_id[:8])
            explanation = generate_reasoning_with_groq(order_dict, ranked[0], demand_result["weights"])
            logger.info("[%s] Explanation generated (%d chars)", trace_id[:8], len(explanation))

        event_bus.publish_sync(create_event(
            sender_agent="ExplanationAgent",
            event_type="EXPLANATION_GENERATED",
            data={
                "explanation_length": len(explanation),
                "message": f"Explanation generated ({len(explanation)} chars)"
            },
            trace_id=trace_id,
        ))

        event_bus.publish_sync(create_event(
            sender_agent="ExplanationAgent",
            event_type="AGENT_STATUS",
            data={"agent": "ExplanationAgent", "status": "done", "message": "LLM reasoning complete"},
            trace_id=trace_id,
        ))

        event_bus.publish_sync(create_event(
            sender_agent="Orchestrator",
            event_type="AGENT_STATUS",
            data={"agent": "Orchestrator", "status": "done", "message": f"Order {order_id} ready for approval"},
            trace_id=trace_id,
        ))

        order_state = {
            "trace_id": trace_id,
            "order_id": order_id,
            "order_data": order_dict,
            "candidates": ranked,
            "weights": demand_result["weights"],
            "selected_option": ranked[0] if ranked else None,
            "explanation": explanation,
            "status": "PENDING_APPROVAL",
            "approval_status": "PENDING",
            "agent_events": [e.model_dump() for e in event_bus.get_events_by_trace(trace_id)],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._orders[order_id] = order_state

        return {
            "status": "success",
            "trace_id": trace_id,
            "order_id": order_id,
            "order_status": "PENDING_APPROVAL",
            "selected_option": ranked[0] if ranked else None,
            "all_candidates": ranked,
            "total_candidates": len(ranked),
            "feasible_count": sum(1 for c in ranked if c.get("lead_time_days", 999) <= order_dict.get("max_lead_time_days", 999)),
            "criteria_weights": demand_result["weights"],
            "explanation": explanation,
            "agent_events": order_state["agent_events"],
        }

    def approve_order(self, order_id: str, action: str, notes: str = "") -> dict:
        order_state = self._orders.get(order_id)
        if not order_state:
            return {"error": f"Order {order_id} not found"}

        trace_id = order_state["trace_id"]
        selected = order_state.get("selected_option", {})

        if action.upper() == "APPROVE":
            execution_result = self._execute_order(order_state)

            if execution_result.get("success"):
                order_state["status"] = "EXECUTED"
                order_state["approval_status"] = "APPROVED"
                order_state["execution_result"] = execution_result
                event_bus.publish_sync(create_event(
                    sender_agent="HumanOperator",
                    event_type="EXECUTION_APPROVED",
                    data={"notes": notes, "execution": execution_result},
                    trace_id=trace_id,
                ))
                return {
                    "order_id": order_id,
                    "status": "EXECUTED",
                    "executed_option": selected,
                    "execution_result": execution_result,
                    "message": f"Order {order_id} approved and executed.",
                }
            else:
                order_state["status"] = "EXECUTION_FAILED"
                order_state["approval_status"] = "APPROVED"
                order_state["execution_result"] = execution_result
                return {
                    "order_id": order_id,
                    "status": "EXECUTION_FAILED",
                    "executed_option": selected,
                    "execution_result": execution_result,
                    "message": f"Order {order_id} approved but execution failed: {execution_result.get('error')}",
                }
        else:
            order_state["status"] = "REJECTED"
            order_state["approval_status"] = "REJECTED"
            event_bus.publish_sync(create_event(
                sender_agent="HumanOperator",
                event_type="EXECUTION_REJECTED",
                data={"notes": notes},
                trace_id=trace_id,
            ))
            return {
                "order_id": order_id,
                "status": "REJECTED",
                "executed_option": None,
                "message": f"Order {order_id} rejected.",
            }

    def _execute_order(self, order_state: dict) -> dict:
        """Execute the approved order by placing supplier orders or reserving warehouse stock."""
        selected = order_state.get("selected_option", {})
        order_data = order_state.get("order_data", {})
        strategy = selected.get("strategy_name", "")
        source = selected.get("source", "")
        sku = order_data.get("part_id", "")
        qty = selected.get("fulfilled_qty", 0)
        customer_id = order_data.get("customer_id", "UNKNOWN")
        priority = order_data.get("priority", "MEDIUM")

        if "Warehouse" in strategy:
            if db.inventory.execute_order(order_state["order_id"], sku, qty, source):
                logger.info("[EXECUTION] Deducted %d units of %s from warehouse %s", qty, sku, source)
                return {
                    "success": True,
                    "method": "warehouse_deduction",
                    "sku": sku,
                    "quantity": qty,
                    "warehouse": source,
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to deduct {qty} units of {sku} from {source}",
                    "method": "warehouse_deduction",
                }
        elif "Supplier" in strategy:
            try:
                from mocks.supplier_client import SupplierClient
                client = SupplierClient()
                speed_mode = "express" if priority in ("CRITICAL", "HIGH") else "standard"
                result = client.place_seller_order(
                    supplier_id=source,
                    buyer_id=customer_id,
                    sku=sku,
                    quantity=qty,
                    priority=priority,
                    transit_speed_mode=speed_mode,
                )
                logger.info("[EXECUTION] Placed supplier order with %s: %s", source, result.get("order_id"))
                return {
                    "success": True,
                    "method": "supplier_order",
                    "supplier_order_id": result.get("order_id"),
                    "sku": sku,
                    "quantity": qty,
                    "supplier": source,
                }
            except Exception as e:
                logger.error("[EXECUTION] Supplier order failed: %s", e)
                return {
                    "success": False,
                    "error": str(e),
                    "method": "supplier_order",
                }
        else:
            return {
                "success": False,
                "error": f"Unknown strategy: {strategy}",
                "method": "unknown",
            }

    def get_order(self, order_id: str) -> Optional[dict]:
        return self._orders.get(order_id)

    def get_all_orders(self) -> list:
        return [
            {
                "order_id": oid,
                "status": o["status"],
                "approval_status": o["approval_status"],
                "customer_id": o["order_data"].get("customer_id"),
                "part_id": o["order_data"].get("part_id"),
                "created_at": o["created_at"],
            }
            for oid, o in self._orders.items()
        ]

    def get_agent_status(self) -> dict:
        return {
            "system_status": "OPERATIONAL",
            "active_graph_nodes": [
                "DemandAgent",
                "RankingEngine",
                "ExplanationAgent",
                "Orchestrator",
            ],
            "agents": {
                "DemandAgent": {"status": "HEALTHY", "last_event": "ORDER_RECEIVED"},
                "RankingEngine": {"status": "HEALTHY", "last_event": "TOPSIS_COMPLETED"},
                "ExplanationAgent": {"status": "HEALTHY", "last_event": "EXPLANATION_GENERATED"},
                "Orchestrator": {"status": "HEALTHY", "last_event": "ORDER_PROCESSED"},
            },
            "total_orders_processed": len(self._orders),
        }


orchestrator = Orchestrator()
