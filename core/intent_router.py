import os
import re
import json
import uuid
import asyncio
from typing import Dict, Any, Optional
from pydantic import ValidationError
from core.schemas import OrderRequest, AgentEvent
from core.event_bus import event_bus

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


INTENT_EXTRACTION_PROMPT = """
You are an expert Autonomous Supply Chain Intent Parser.
Your task is to parse unstructured, messy incoming emails or customer requests and extract strict structured JSON parameters.

Extract the following JSON fields:
- "order_id": (string, e.g. "ORD-YYYY-XXXX" or extract if mentioned, otherwise generate a unique identifier like "ORD-" + 6 random chars)
- "customer_id": (string, customer name or code, e.g. "Tesla", "Boeing", "CUST-101")
- "part_id": (string, SKU or part number, e.g. "PART-X100", "A-102", "MOTOR-V6")
- "requested_qty": (integer, quantity requested by customer, e.g. 50)
- "max_lead_time_days": (integer, maximum allowed days for delivery, e.g. 3)
- "priority": (string, must be strictly one of: "LOW", "MEDIUM", "HIGH", "CRITICAL")
- "notes": (string, brief summary of specific customer requirements or context)

Respond ONLY with a valid JSON object. Do not include markdown code block formatting like ```json or any extra commentary.
"""


def _heuristic_fallback_parser(text: str, default_customer: Optional[str] = None, default_priority: Optional[str] = None) -> Dict[str, Any]:
    """
    Deterministic rule-based fallback parser for offline execution or when Gemini API is unreachable.
    Extracts order parameters using robust pattern matching.
    """
    clean_text = text.strip()
    
    # 1. Extract Quantity
    qty_match = re.search(r'(\d+)\s*(?:units?|pcs?|pieces?|items?|qty|quantit(?:y|ies))', clean_text, re.IGNORECASE)
    if not qty_match:
        # Check for numbers before part IDs or standalone numbers
        num_matches = re.findall(r'\b\d+\b', clean_text)
        qty = int(num_matches[0]) if num_matches else 10
    else:
        qty = int(qty_match.group(1))

    # 2. Extract Lead Time
    lead_time_match = re.search(r'(\d+)\s*(?:days?|day|d)\b', clean_text, re.IGNORECASE)
    if not lead_time_match:
        lead_time_match = re.search(r'(?:within|in|max|deadline|deliver\s+by)\s*(\d+)', clean_text, re.IGNORECASE)
    lead_time = int(lead_time_match.group(1)) if lead_time_match else 5

    # 3. Extract Priority
    if default_priority:
        priority = default_priority.upper()
    elif re.search(r'\b(critical|urgent|asap|emergency)\b', clean_text, re.IGNORECASE):
        priority = "CRITICAL"
    elif re.search(r'\b(high|rush|expedite)\b', clean_text, re.IGNORECASE):
        priority = "HIGH"
    elif re.search(r'\b(low|flexible|non-urgent)\b', clean_text, re.IGNORECASE):
        priority = "LOW"
    else:
        priority = "MEDIUM"

    # 4. Extract Part ID
    sku_match = re.search(r'\b([A-Za-z0-9]{2,10}-[A-Za-z0-9]{2,10})\b', clean_text)
    if sku_match:
        part_id = sku_match.group(1).upper()
    else:
        part_match = re.search(r'(?:part|sku|item|component|model)\s*(?:#|id|code)?\s*[:\-]?\s*([A-Za-z0-9_\-]+)', clean_text, re.IGNORECASE)
        if part_match:
            part_id = part_match.group(1).upper()
            if not part_id.startswith("PART-") and not part_id.startswith("SKU-"):
                part_id = f"PART-{part_id}"
        else:
            sku_match2 = re.search(r'\b([A-Z]{1,5}-?[0-9]{2,5}[A-Z0-9]*)\b', clean_text)
            part_id = sku_match2.group(1).upper() if sku_match2 else "PART-A100"

    # 5. Extract Customer ID
    if default_customer:
        customer_id = default_customer
    else:
        cust_match = re.search(r'(?:customer|client|from|for|account)\s*[:\-]?\s*([A-Za-z0-9_\-\s]{2,25}?)(?:,|\.|\n|within|in|need|require|urgent|priority|$)', clean_text, re.IGNORECASE)
        if cust_match and cust_match.group(1).strip():
            customer_id = cust_match.group(1).strip()
        else:
            customer_id = "CUST-DEFAULT"


    # 6. Extract or generate Order ID
    order_match = re.search(r'(?:order|po|req)\s*(?:#|id|number)?\s*[:\-]?\s*([A-Za-z0-9_\-]+)', clean_text, re.IGNORECASE)
    if order_match and any(c.isdigit() for c in order_match.group(1)):
        order_id = order_match.group(1).upper()
    else:
        order_id = f"ORD-{uuid.uuid4().hex[:6].upper()}"

    return {
        "order_id": order_id,
        "customer_id": customer_id,
        "part_id": part_id,
        "requested_qty": max(1, qty),
        "max_lead_time_days": max(1, lead_time),
        "priority": priority,
        "notes": f"Rule-based parsed from: {clean_text[:80]}..."
    }


class IntentRouter:
    """
    Converts unstructured email/text customer requests into validated OrderRequest parameters
    using Gemini API with structured output and fallback heuristic engine.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self._client = None
        if self.api_key and GENAI_AVAILABLE:
            try:
                self._client = genai.Client(api_key=self.api_key)
            except Exception:
                self._client = None

    async def parse_unstructured_order(
        self,
        raw_text: str,
        trace_id: Optional[str] = None,
        default_customer: Optional[str] = None,
        override_priority: Optional[str] = None
    ) -> OrderRequest:
        """
        Parses raw text/email into a validated OrderRequest.
        Emits AgentEvent on event_bus.
        """
        if not trace_id:
            trace_id = f"trace-{uuid.uuid4().hex[:8]}"

        extracted_dict: Optional[Dict[str, Any]] = None
        parse_method = "HEURISTIC_FALLBACK"

        # Attempt Gemini LLM Extraction if client is configured
        if self._client:
            for attempt in range(2):  # Retry with backoff
                try:
                    prompt = f"{INTENT_EXTRACTION_PROMPT}\n\nIncoming Customer Request:\n\"\"\"{raw_text}\"\"\""
                    response = await asyncio.to_thread(
                        self._client.models.generate_content,
                        model='gemini-2.5-flash',
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json"
                        )
                    )
                    if response and response.text:
                        raw_json = response.text.strip()
                        # Clean code fence if present
                        if raw_json.startswith("```json"):
                            raw_json = raw_json[7:]
                        if raw_json.endswith("```"):
                            raw_json = raw_json[:-3]
                        extracted_dict = json.loads(raw_json)
                        parse_method = "GEMINI_JSON_EXTRACTION"
                        break
                except Exception as e:
                    if attempt == 0:
                        await asyncio.sleep(0.5)
                    else:
                        extracted_dict = None

        # Fallback to deterministic regex parser if Gemini unavailable or failed
        if not extracted_dict:
            extracted_dict = _heuristic_fallback_parser(
                raw_text,
                default_customer=default_customer,
                default_priority=override_priority
            )
            parse_method = "RULE_BASED_FALLBACK"

        # Apply overrides if provided
        if override_priority:
            extracted_dict["priority"] = override_priority.upper()
        if default_customer and (not extracted_dict.get("customer_id") or extracted_dict.get("customer_id") == "CUST-DEFAULT"):
            extracted_dict["customer_id"] = default_customer

        # Ensure priority is strictly valid
        if extracted_dict.get("priority", "").upper() not in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            extracted_dict["priority"] = "MEDIUM"

        order = OrderRequest(
            order_id=str(extracted_dict.get("order_id", f"ORD-{uuid.uuid4().hex[:6].upper()}")),
            customer_id=str(extracted_dict.get("customer_id", "CUSTOMER-UNKNOWN")),
            part_id=str(extracted_dict.get("part_id", "PART-GENERIC")),
            requested_qty=int(extracted_dict.get("requested_qty", 1)),
            max_lead_time_days=int(extracted_dict.get("max_lead_time_days", 5)),
            priority=str(extracted_dict.get("priority", "MEDIUM")).upper(),
            raw_text=raw_text
        )

        # Emit audit event conforming to .cursorrules
        event = AgentEvent(
            trace_id=trace_id,
            sender_agent="DemandIntentAgent",
            recipient_agent="Orchestrator",
            event_type="ORDER_INTENT_PARSED",
            data={
                "order": order.model_dump(),
                "parse_method": parse_method,
                "raw_text_length": len(raw_text)
            }
        )
        await event_bus.publish(event)

        return order


# Global instance
intent_router = IntentRouter()
