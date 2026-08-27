"""
Explanation Agent
=================
Generates human-readable reasoning for the TOPSIS-selected fulfillment strategy.
Falls back to a deterministic rationale if Groq/LLM is unavailable.
"""

from __future__ import annotations

import os
from typing import Optional


def generate_recommendation_rationale(order_payload: dict, top_winner: dict, weights: Optional[dict] = None) -> str:
    """Deterministic rule-based explanation for the selected fulfillment strategy."""
    if not top_winner:
        return "No suitable fulfillment candidate was found for this order."

    candidate_id = top_winner.get("candidate_id", "Unknown")
    source = top_winner.get("source") or top_winner.get("warehouse_id", "Unknown Source")
    score = top_winner.get("topsis_score", 0.0)
    lead_time = top_winner.get("lead_time_days", "N/A")
    cost = top_winner.get("unit_cost", "N/A")
    total_cost = top_winner.get("total_cost", "N/A")
    sku = top_winner.get("sku", top_winner.get("item_sku", "N/A"))
    can_fulfill = top_winner.get("can_fulfill", True)
    fulfillment_type = top_winner.get("fulfillment_type", "Standard")
    priority = order_payload.get("priority", "MEDIUM").upper()

    weight_context = ""
    if weights:
        top_weight = max(weights, key=weights.get)
        weight_context = f" The optimization prioritized **{top_weight.replace('_', ' ')}** ({int(weights[top_weight]*100)}% weight) based on the {priority} priority level."

    stock_note = ""
    if not can_fulfill:
        avail = top_winner.get("available_stock", 0)
        qty = order_payload.get("requested_qty", 0)
        stock_note = f" ⚠️ Note: Only {avail} units available vs {qty} requested — partial fulfillment or split sourcing recommended."

    rationale = (
        f"✅ **Selected**: {candidate_id} via {source} | Strategy: {fulfillment_type}\n\n"
        f"📊 **TOPSIS Score**: {score:.4f} — ranked #1 among all evaluated options.\n\n"
        f"📦 **SKU**: {sku} | Unit Cost: ${cost} | Total Cost: ${total_cost}\n\n"
        f"🚚 **Lead Time**: {lead_time} day(s) to fulfillment.{weight_context}{stock_note}"
    )
    return rationale


def generate_reasoning_with_groq(order_payload: dict, top_winner: dict, weights: Optional[dict] = None) -> str:
    """
    Groq LPU-powered reasoning (falls back to deterministic rationale if unavailable).
    Signature matches main.py call: generate_reasoning_with_groq(order, selected, weights)
    """
    groq_api_key = os.getenv("GROQ_API_KEY")

    if groq_api_key:
        try:
            from groq import Groq  # type: ignore
            client = Groq(api_key=groq_api_key)

            weight_str = ", ".join(f"{k}: {int(v*100)}%" for k, v in (weights or {}).items())
            prompt = (
                f"You are a supply chain AI assistant. Explain in 3 concise sentences why the following "
                f"fulfillment candidate was selected for this order.\n\n"
                f"Order: Part {order_payload.get('part_id')}, Qty {order_payload.get('requested_qty')}, "
                f"Priority {order_payload.get('priority')}, Max Lead Time {order_payload.get('max_lead_time_days')} days.\n"
                f"Selected Candidate: {top_winner.get('candidate_id')} from {top_winner.get('source', top_winner.get('warehouse_id'))}, "
                f"TOPSIS Score {top_winner.get('topsis_score', 0):.4f}, "
                f"Lead Time {top_winner.get('lead_time_days')} days, Cost ${top_winner.get('unit_cost')}.\n"
                f"TOPSIS weight profile used: {weight_str}.\n\n"
                f"Provide a brief, professional rationale."
            )
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3,
            )
            ai_text = response.choices[0].message.content.strip()
            return f"🤖 **AI Reasoning (Groq LPU)**:\n\n{ai_text}"
        except Exception:
            pass  # Fall through to deterministic fallback

    return generate_recommendation_rationale(order_payload, top_winner, weights)
