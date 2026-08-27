import os
import re
import json
import logging
import time

logger = logging.getLogger("explanation_agent")

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


def _sanitize_field(value: str, max_len: int = 100) -> str:
    """Sanitize a field before embedding in LLM prompt."""
    if not isinstance(value, str):
        value = str(value)
    value = value.strip()[:max_len]
    value = re.sub(r'[<>"{}]', '', value)
    return value


def generate_reasoning_with_groq(order: dict, optimal_option: dict, weights: dict = None) -> str:
    part_id = _sanitize_field(order.get("part_id", "Unknown Part"))
    customer_id = _sanitize_field(order.get("customer_id", "Unknown Customer"))
    priority = _sanitize_field(order.get("priority", "MEDIUM"), max_len=10)
    qty = order.get("requested_qty", 0)
    strategy = _sanitize_field(optimal_option.get("strategy_name", "N/A"))
    source = _sanitize_field(optimal_option.get("source", "N/A"))
    unit_cost = optimal_option.get("unit_cost", 0)
    total_cost = optimal_option.get("total_cost", 0)
    lead_time = optimal_option.get("lead_time_days", 0)
    score = optimal_option.get("topsis_score", 0.0)

    if not isinstance(qty, (int, float)) or qty <= 0:
        qty = 0
    if not isinstance(unit_cost, (int, float)):
        unit_cost = 0
    if not isinstance(total_cost, (int, float)):
        total_cost = 0
    if not isinstance(lead_time, (int, float)):
        lead_time = 0
    if not isinstance(score, (int, float)):
        score = 0

    client = None
    api_key = os.getenv("GROQ_API_KEY")
    if GROQ_AVAILABLE and api_key:
        try:
            client = Groq(api_key=api_key)
        except Exception:
            client = None

    if client:
        prompt = f"""Write ONE sentence (max 25 words) explaining why this option was chosen for this supply chain order.

{qty}x {part_id}, priority={priority}, chosen={strategy} from {source}, ${total_cost:.2f}, {lead_time}d lead, score={score:.4f}"""

        for attempt in range(3):
            try:
                response = client.chat.completions.create(
                    model="qwen/qwen3.8-27b",
                    messages=[
                        {"role": "system", "content": "You are a supply chain analyst. Be extremely concise. Max 25 words per response. No fluff."},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=100,
                    temperature=0.3,
                )
                result = response.choices[0].message.content.strip()
                # Hard truncate to ~120 chars (roughly 2 short sentences)
                if len(result) > 120:
                    result = result[:117].rsplit(' ', 1)[0] + "..."
                if result and len(result) > 20:
                    logger.info("[EXPLANATION] Generated %d chars", len(result))
                    return result
            except Exception as e:
                logger.warning("[EXPLANATION] Attempt %d failed: %s", attempt + 1, e)
                if attempt < 2:
                    time.sleep(0.5 * (attempt + 1))

    explanation = (
        f"Selected {strategy} from {source} for {qty} units of {part_id} "
        f"(customer: {customer_id}, priority: {priority}). "
        f"Total cost: ${total_cost:.2f} with {lead_time}-day lead time. "
        f"TOPSIS score: {score:.4f} — best balance of cost, speed, and reliability."
    )
    return explanation
