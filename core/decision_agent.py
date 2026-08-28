"""
DecisionAgent — the final decision-maker in the pipeline.

The Orchestrator delegates the *last call* here: interpreting the special
instructions / prompt in natural language, hard-applying any explicit
constraints (price caps, lead-time caps, minimum reliability), and then
selecting the final fulfillment option. It still *considers* the TOPSIS score
but is not bound to it: when the prompt's language demands a specific priority
(e.g. "cheapest", "fastest", "most reliable", "price below 1000"), the agent
adjusts the decision accordingly — so the outcome is a decision, not just a
formula.

Two tiers:
  * Deterministic tier — always works offline. Parses the prompt into
    constraints + emphasis and re-derives TOPSIS weights from that language.
  * LLM tier — when GROQ_API_KEY is present, an LLM reviews the prompt plus
    the shortlist and makes the explicit final pick + justification.
"""
import logging
import re
import json
from typing import Optional, Dict, Any, List, Tuple

logger = logging.getLogger("decision_agent")


# ---------------------------------------------------------------------------
# 1. Prompt interpretation (deterministic, offline)
# ---------------------------------------------------------------------------

def interpret_prompt(prompt: Optional[str], qty: int = 1) -> Dict[str, Any]:
    """Turn the special-instructions text into structured decision inputs."""
    if not prompt:
        prompt = ""
    text = str(prompt).lower()

    constraints: Dict[str, float] = {}

    # --- Price per unit: "price below 1000", "under $1000/unit", "per unit < 500" ---
    # Prefer an /unit or "per part" qualifier.
    unit_patterns = [
        r"(?:price|unit|cost per unit|per unit|per part|price per)\s*(?:is|should be|must be)?\s*(?:below|under|less\s*than|<)?\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:/unit|per\s*unit|each)?",
        r"\$?\s*([\d,]+(?:\.\d+)?)\s*(?:/unit|per\s*unit|per\s*part|each)\b",
    ]
    for pat in unit_patterns:
        m = re.search(pat, text)
        if m:
            constraints["unit_price_max"] = float(m.group(1).replace(",", ""))
            break
    # "price below 1000" without a per-unit qualifier — treat as unit cap unless
    # total words are present.
    if "unit_price_max" not in constraints:
        m = re.search(r"price\s*(?:is|should be|must be)?\s*(?:below|under|less\s*than|at most|<)?\s*\$?\s*([\d,]+(?:\.\d+)?)", text)
        if m:
            constraints["unit_price_max"] = float(m.group(1).replace(",", ""))

    # --- Total budget: "budget", "total under", "keep it under", "not more than" ---
    total_patterns = [
        r"(?:total|budget|overall|spend|max\s*(?:total)?\s*cost|keep\s*it\s*under|not\s*more\s*than)\s*(?:cost|budget|spend|under)?\s*(?:of|at|below|under)?\s*\$?\s*([\d,]+(?:\.\d+)?)",
        r"<=?\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:total|overall)?\b",
    ]
    if "unit_price_max" not in constraints:  # don't double-count a bare number
        for pat in total_patterns:
            m = re.search(pat, text)
            if m:
                constraints["total_cost_max"] = float(m.group(1).replace(",", ""))
                break

    # --- Lead-time cap: "within 3 days", "deliver in 2 days", "<= 4 days" ---
    m = re.search(r"within\s*([\d]+)\s*(?:days?|d|business\s*days?)", text) or \
        re.search(r"deliver(?:y)?\s*(?:in|within)\s*([\d]+)\s*(?:days?|d)", text) or \
        re.search(r"<=?\s*([\d]+)\s*(?:days?|d)\b", text) or \
        re.search(r"\bby\s*([\d]+)\s*(?:days?|d)\b", text)
    if m:
        constraints["lead_days_max"] = float(m.group(1))

    # --- Minimum reliability: "at least 0.95 reliable", "95% reliability" ---
    m = re.search(r"(?:reliability|reliable).{0,20}?(?:>=|at least|min|≥)?\s*([\d.]+)\s*%", text)
    if m:
        constraints["min_reliability"] = float(m.group(1)) / 100.0

    # --- Language emphasis (soft priorities) ---
    words = {
        "fastest":  re.search(r"\bfastest\b|\basap\b|\bimmediately\b|\brush\b|\burst\b|\burgent\b", text) is not None,
        "fast":     re.search(r"\bfast\b|\bquick\b|\bspeed\b|\bsoon\b|\bexpedite\b|\bprioritize\s*speed\b", text) is not None,
        "cheapest": re.search(r"\bcheapest\b|\bcheap\b|\blow\s*cost\b|\bminimize\s*cost\b|\best\s*price\b|\bbest\s*value\b|\bcost\s*effective\b", text) is not None,
        "reliable": re.search(r"\breliable\b|\breliability\b|\btrusted\b|\bhigh\s*quality\b|\bdependable\b", text) is not None,
        "critical": re.search(r"\bcritical\b|\bmust\b|\brequired\b|\bmandatory\b|\bhard\s*constraint\b|\bessential\b", text) is not None,
        "picky_price": "price" in text or "unit" in text or "cost" in text or "budget" in text,
    }

    emphasis: Dict[str, float] = {}
    if words["fastest"] or words["fast"]:
        emphasis["lead_time"] = 0.5
    if words["cheapest"] or words["picky_price"]:
        emphasis.setdefault("cost", 0.5)
    if words["reliable"]:
        emphasis["reliability"] = 0.5

    intention = "standard"
    if words["cheapest"]:
        intention = "lowest_cost"
    elif words["fastest"] or words["fast"]:
        intention = "fastest"
    elif words["reliable"]:
        intention = "most_reliable"
    elif emphasis.get("cost"):
        intention = "cost_aware"
    elif words["critical"]:
        intention = "critical"

    return {
        "constraints": constraints,
        "emphasis": emphasis,
        "intention": intention,
        "prompt": prompt,
        "words": words,
    }


def apply_constraints(candidates: List[Dict], constraints: Dict[str, float]) -> Tuple[List[Dict], int]:
    """Hard-filter candidates against numeric constraints. Returns (kept, dropped)."""
    if not constraints:
        return candidates, 0
    removed = 0
    kept = []
    for c in candidates:
        unit = c.get("unit_cost", 0.0)
        total = c.get("total_cost", 0.0)
        lead = c.get("lead_time_days", 999)
        rel = c.get("reliability_score", 0.0)
        if "unit_price_max" in constraints and unit > constraints["unit_price_max"]:
            removed += 1
            continue
        if "total_cost_max" in constraints and total > constraints["total_cost_max"]:
            removed += 1
            continue
        if "lead_days_max" in constraints and lead > constraints["lead_days_max"]:
            removed += 1
            continue
        if "min_reliability" in constraints and rel < constraints["min_reliability"]:
            removed += 1
            continue
        kept.append(c)
    return kept, removed


def agent_tune_weights(base_weights: Dict[str, float], emphasis: Dict[str, float]) -> Dict[str, float]:
    """Shift TOPSIS weights toward whatever the prompt emphasizes."""
    w = dict(base_weights)
    if not emphasis:
        return w
    boost = {
        "cost": 0.25,
        "lead_time": 0.25,
        "reliability": 0.20,
    }
    # Boost emphasized criteria; rebalance the rest to keep the sum at 1.0.
    extra = 0.0
    for key, val in emphasis.items():
        if key in w:
            w[key] += boost.get(key, 0.2)
            extra += boost.get(key, 0.2)
    # Rebalance the non-emphasized criteria proportionally downward.
    unboosted = [k for k in w if w[k] < 1.0 and k not in emphasis]
    if unboosted and extra > 0:
        total_unboosted = sum(w[k] for k in unboosted)
        if total_unboosted > 0:
            for k in unboosted:
                w[k] -= extra * (w[k] / total_unboosted)
    # Clamp + renormalize.
    for k in w:
        w[k] = max(0.0, w[k])
    total = sum(w.values())
    if total > 0:
        w = {k: round(v / total, 4) for k, v in w.items()}
    return w


# ---------------------------------------------------------------------------
# 2. LLM decision tier (optional, needs GROQ_API_KEY)
# ---------------------------------------------------------------------------

def _describe(c: Dict, idx: int) -> str:
    return (f"{idx}. {c.get('strategy_name')} | qty={c.get('fulfilled_qty')} "
            f"unit=${c.get('unit_cost')} total=${c.get('total_cost')} "
            f"lead={c.get('lead_time_days')}d rel={c.get('reliability_score')} "
            f"topsis={c.get('topsis_score')}")


def llm_make_decision(order: Dict, ranked: List[Dict], intention: str,
                      constraints: Dict[str, float], base_weights: Dict[str, float],
                      prompt: Optional[str], max_candidates: int = 6,
                      feedback: Optional[str] = None) -> Optional[Dict]:
    """Ask an LLM to pick the final option from the TOPSIS shortlist."""
    import os
    try:
        from groq import Groq
    except ImportError:
        return None
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    try:
        client = Groq(api_key=api_key)
    except Exception:
        return None

    part = order.get("part_id", "unknown")
    qty = order.get("requested_qty", 0)
    shortlist = ranked[:max_candidates]
    lines = "\n".join(_describe(c, i + 1) for i, c in enumerate(shortlist))
    constraint_str = json.dumps(constraints) if constraints else "none"
    special = str(prompt or "").strip() or "no special instructions"

    system = (
        "You are the final decision-maker for a supply chain fulfillment agent. "
        "You receive a list of candidate options (each with quantity, unit cost, "
        "total cost, lead time in days, reliability, and a TOPSIS score) plus the "
        "customer's special instructions. Decide which SINGLE option best fulfills "
        "the order. Honor any hard constraints (price caps, delivery time, reliability) "
        "strictly. Use the TOPSIS score as guidance but let the SPECIFIC LANGUAGE of "
        "the instructions drive the priority (cheapest / fastest / most reliable / "
        "best value). Reply ONLY with a JSON object with keys "
        "\"selected\" (the index number you chose) and \"rationale\" (one sentence "
        "explaining the decision in terms of the instructions)."
    )
    feedback_block = (
        f"\nThe customer REJECTED the previous top option because: \"{feedback}\". "
        f"Choose a different option that better addresses this concern.\n"
    ) if feedback else ""
    user = (
        f"Order: {qty}x {part} for customer {order.get('customer_id')}, "
        f"priority {order.get('priority')}.\n"
        f"Special instructions: \"{special}\"\n"
        f"Hard constraints parsed: {constraint_str}\n"
        f"Base priority weights: {json.dumps(base_weights)} "
        f"(cost, lead_time, reliability)\n"
        f"{feedback_block}"
        f"Candidate shortlist:\n{lines}\n\n"
        "Return the JSON decision now."
    )

    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model="qwen/qwen3.8-27b",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                max_tokens=250,
                temperature=0.2,
            )
            out = resp.choices[0].message.content.strip()
            # Extract JSON object in case the model wraps it in prose.
            m = re.search(r"\{.*\}", out, re.DOTALL)
            if not m:
                logger.warning("[DECISION] LLM returned non-JSON: %s", out[:120])
                continue
            data = json.loads(m.group(0))
            idx = int(data.get("selected", 0))
            if 1 <= idx <= len(shortlist):
                return {"option": shortlist[idx - 1], "rationale": str(data.get("rationale", ""))}
        except Exception as e:
            logger.warning("[DECISION] LLM attempt %d failed: %s", attempt + 1, e)
            if attempt < 2:
                import time
                time.sleep(0.5 * (attempt + 1))
    return None


# ---------------------------------------------------------------------------
# 3. Public entry point
# ---------------------------------------------------------------------------

def decide(order: Dict, ranked: List[Dict], base_weights: Dict[str, float],
           feedback: Optional[str] = None) -> Dict[str, Any]:
    """
    Make the final decision for an order.
    Returns {selected_option, rationale, intention, constraints, final_weights, all_ranked}
    When `feedback` is provided (a rejection reason), it is folded into the prompt so
    the deterministic intent parser and the LLM tier both steer away from the prior pick.
    """
    if not ranked:
        return {"selected_option": None, "rationale": "No candidates available to decide from.",
                "intention": "none", "constraints": {}, "final_weights": base_weights,
                "all_ranked": [], "dropped_by_constraint": 0}

    prompt = order.get("notes") or ""
    if feedback:
        prompt = f"{prompt}. Rejected previous option because: {feedback}"
    qty = order.get("requested_qty", 1)
    parsed = interpret_prompt(prompt, qty)

    # Hard-apply explicit numeric constraints from the prompt.
    kept, dropped = apply_constraints(ranked, parsed["constraints"])
    if not kept:
        # Nothing survives the hard constraints — surface that honestly.
        kept = ranked
        blocked = True
    else:
        blocked = False

    # Re-tune weights toward what the prompt's language emphasizes.
    final_weights = agent_tune_weights(base_weights, parsed["emphasis"])

    # Re-rank the surviving candidates with the prompt-tuned weights.
    from core.topsis import run_topsis_optimization
    tuned_ranked = run_topsis_optimization(kept, final_weights)

    # Let the LLM make the explicit final call when available; else fall back
    # to the (already prompt-tuned) TOPSIS winner.
    llm = llm_make_decision(order, tuned_ranked, parsed["intention"],
                            parsed["constraints"], final_weights, prompt,
                            feedback=feedback)
    if llm:
        selected = llm["option"]
        rationale = f"[DecisionAgent] {llm['rationale']}"
    else:
        selected = tuned_ranked[0]
        if blocked:
            rationale = ("No option satisfies every stated constraint; best feasible "
                         f"option chosen. Intention: {parsed['intention']}.")
        else:
            rationale = (f"Ranked by TOPSIS with weights tuned for intent "
                         f"'{parsed['intention']}' (cost={final_weights.get('cost')}, "
                         f"lead={final_weights.get('lead_time')}, "
                         f"rel={final_weights.get('reliability')}).")

    if blocked:
        dropped = 0  # nothing was truly dropped; all violated some constraint

    return {
        "selected_option": selected,
        "rationale": rationale,
        "intention": parsed["intention"],
        "constraints": parsed["constraints"],
        "final_weights": final_weights,
        "all_ranked": tuned_ranked,
        "dropped_by_constraint": dropped,
        "llm_decided": bool(llm),
    }
