# AgentXcelerate — Hackathon Q&A (Grounded in the Code)

Answers reference actual files: `core/orchestrator.py`, `core/decision_agent.py`,
`core/topsis.py`, `core/intent_router.py`, `core/event_bus.py`, `core/database.py`,
`agents/demand_agent.py`, `mocks/suppliers.py`, `mocks/supplier_server.py`,
`core/geocoder.py`.

---

## 1. Architecture & Design

**Q: What is this project, in one sentence?**
An event-driven, multi-agent autonomous supply-chain fulfillment system that takes a
customer order (structured or free-text), generates fulfillment options from warehouses
and suppliers, ranks them with TOPSIS, then makes a final decision driven by the
customer's own language ("cheapest", "fastest", "most reliable"), with a human
approval gate before execution.

**Q: What's the architecture?**
A pipeline of collaborating agents glued together by an **event bus** (audit log +
pub/sub) and an **orchestrator** that owns the workflow and state. Every agent talks
through typed `AgentEvent` messages with a shared `trace_id` for end-to-end tracing.

**Q: Which agents exist and what does each do?**
- **Orchestrator** (`core/orchestrator.py`) — receives order, drives the pipeline, holds order state.
- **DemandAgent** (`agents/demand_agent.py`) — turns an order into candidate fulfillment options (warehouses + suppliers), applies budget caps.
- **RankingEngine** (`core/topsis.py`) — multi-criteria TOPSIS ranking of candidates.
- **DecisionAgent** (`core/decision_agent.py`) — interprets free-text instructions, applies hard constraints, re-tunes weights, makes the final pick (optionally via LLM).
- **DemandIntentAgent** (`core/intent_router.py`) — parses unstructured email/text into a structured order (Gemini LLM with a regex fallback).
- **ExplanationAgent** (`agents/explanation_agent.py`) — generates a natural-language justification via Groq.

**Q: How do agents communicate?**
Through the **event bus** (`core/event_bus.py`). Every message is an `AgentEvent`
Pydantic model with `trace_id`, `timestamp`, `sender_agent`, `recipient_agent`,
`event_type`, and `data`. Publishing appends to history and notifies subscribers
synchronously. The `trace_id` lets you reconstruct the full causal chain of one order.

**Q: Why an event bus instead of direct function calls?**
Observability and auditability. The hackathon brief (.cursorrules) mandates every
inter-agent message be a structured `AgentEvent` with a trace_id. You can replay/query
`/traces/{trace_id}/events` to see exactly what each agent did and when.

---

## 2. The Order Pipeline

**Q: Walk me through a full order, end to end.**
1. `POST /process-order` (or `/api/v1/process-order`) receives JSON; if it carries `raw_text`, it goes through the **IntentRouter** to extract structured fields.
2. `Orchestrator.process_order` creates a `trace_id` + `order_id`, publishes `ORDER_RECEIVED`.
3. **DemandAgent** builds candidates: all warehouses holding the SKU + all supplier quotes, computing cost, lead time, reliability.
4. **RankingEngine** runs TOPSIS over the candidates.
5. **DecisionAgent** re-reads the prompt: hard-filters on numeric constraints (budget, price cap, lead time, min reliability), re-tunes weights toward the expressed priority, and picks a winner (optionally with an LLM).
6. **ExplanationAgent** produces a human-readable rationale.
7. State is stored as `PENDING_APPROVAL` — a human approves/rejects via `/approve-execution`.
8. On approve, `_execute_order` either deducts warehouse stock or places a supplier order.

**Q: What is the role of the human in the loop?**
Execution is gated behind approval. The system recommends, the human approves.
`/approve-execution` with `action=APPROVE` triggers `_execute_order`; `REJECT` marks it rejected.

---

## 3. TOPSIS & Ranking

**Q: Why TOPSIS?**
Fulfillment options trade off three competing criteria — **cost, lead time, reliability** —
that don't share units. TOPSIS normalizes each criterion, finds the ideal-best and
ideal-worst points, and scores each option by its Euclidean distance to both (closeness
to best / total distance). The winner is closest to the ideal and farthest from the worst.

**Q: Which criteria does TOPSIS use and which direction is "good"?**
`unit_cost` (minimize), `lead_time_days` (minimize), `reliability_score` (maximize).
The ideal best is `[min cost, min lead, max reliability]`.

**Q: What are the default weights?**
From `_calculate_priority_weights` (by order priority):
- CRITICAL: cost 0.10 / lead 0.60 / reliability 0.30
- HIGH: 0.20 / 0.50 / 0.30
- MEDIUM: 0.35 / 0.35 / 0.30
- LOW: 0.55 / 0.15 / 0.30

Higher priority ⇒ speed weighted more; lower ⇒ cost weighted more.

**Q: How do weights change based on the customer's words?**
`agent_tune_weights` boosts the emphasized criterion (+0.25 cost/lead, +0.20 reliability)
and renormalizes the rest to keep the sum at 1.0, based on keyword emphasis parsed from
the prompt.

---

## 4. Intent Parsing (free-text orders)

**Q: How does free-text turn into a structured order?**
`IntentRouter.parse_unstructured_order` tries **Gemini** (`gemini-2.5-flash`, JSON mode)
first, validating the output. If Gemini is missing/fails, it falls back to a deterministic
regex parser (`_heuristic_fallback_parser`) that extracts quantity, lead time, priority,
part ID, customer, and order ID — so the system works **fully offline**.

**Q: How are priorities inferred from text?**
Keywords map to priority: `critical/urgent/asap/emergency` → CRITICAL;
`high/rush/expedite` → HIGH; `low/flexible/non-urgent` → LOW; else MEDIUM.

**Q: How are hard constraints parsed?**
`DecisionAgent.interpret_prompt` extracts:
- unit price cap — "price below 1000", "under $1000/unit"
- total budget — "budget $5200", "total under 4200"
- lead-time cap — "within 3 days", "deliver in 5d"
- min reliability — "at least 95% reliable"

These become **hard filters** (drop candidates that violate them) before re-ranking.

**Q: How does "cheapest" vs "fastest" vs "most reliable" actually change the outcome?**
The prompt is parsed into an `intention` (lowest_cost / fastest / most_reliable / cost_aware /
standard / critical), which drives both (a) the weight re-tune and (b) the optional LLM
final pick. The DecisionAgent's whole purpose (per its docstring) is to make the outcome a
*decision*, not a formula — the language of the prompt, not just the TOPSIS score, sets priority.

---

## 5. Suppliers & Warehouses (the data)

**Q: What are the three supplier personas?**
From `_PROFILES` in `mocks/suppliers.py`:
- **Supplier A (Primary)** — cheapest (×1.0), full stock (×1.0), slow (10d lead), most reliable (0.97).
- **Supplier B (Express)** — 45% markup (×1.45), partial stock (×0.35), fast (2d), least reliable (0.82).
- **Supplier C (Alt Region)** — 15% markup (×1.15), medium stock (×0.60), mid lead (4d), mid reliability (0.90).

These encode the classic fast/cheap/reliable trade-off triangle.

**Q: How many warehouses, and what do they differ on?**
15 warehouses (e.g. Mumbai West Hub, Nagpur Central Hub, Bengaluru Technology Hub). Each has
`base_lead_days` (Mumbai 1d → Guwahati 5d), a static `reliability` (0.88–0.99), and a regional
price multiplier via `regional_price_multiplier` (tier-1 metros cost more; Mumbai ×1.35,
Indore ×1.0).

**Q: How is cost computed for a warehouse option?**
`unit_cost = base_unit_price × regional_multiplier`; shipping is distance-based last-mile
cost; `total_cost = unit_cost × fulfilled_qty + shipping`.

**Q: How is lead time computed?**
`base_lead_days + ceil(transit_days)`, where `transit_days` comes from
`distance_km_to_transit_days` (haversine distance ÷ ~500 km/day).

**Q: How is reliability adjusted per candidate?**
Base warehouse/supplier reliability, then penalized if lead time exceeds the max lead
(proportional to overage), and penalized further for partial fills (× fill ratio).

---

## 6. Data & Storage

**Q: Where does data live?**
A SQLite DB (`scm.db`) behind a `core/database.py` interface (`db` singleton). Includes
`parts`, `warehouses`, `inventory`, `orders`, `sales`, `buyer_sales_summary`,
`seller_sales_summary`, `demand_price_history`, `macro_sentiment`, `marketing_calendar`,
`fulfillment_candidates`, `topsis_evaluation`, etc. Supplier catalogs are derived from
this central DB and held in memory.

**Q: How is available stock computed?**
`available_qty = on_hand - reserved - damaged` (see the `WarehouseStock` dataclass). This is
a subtle point — the `available` column in SQLite is separate from the derived
`available_qty` the agents actually use.

**Q: What are the running servers?**
Three backends + one frontend:
- `main:app` → main multi-agent SCM API (default 8101)
- `mocks.supplier_server:app` → seller + logistics gateway (default 8001)
- `app:app` → legacy optimizer (`/api/optimize`)
- Vite React frontend (5173), proxying `/api`, `/orders`, `/traces`, etc. to the main backend.

---

## 7. Reliability, Failure & Edge Cases

**Q: What if no candidate satisfies a hard constraint?**
`apply_constraints` drops everything; if the kept list is empty, the DecisionAgent falls back
to the original ranked list with `blocked=True` and picks the best *feasible* option, stating
honestly that no option satisfies every constraint.

**Q: What if no candidates at all?**
DemandAgent emits an "Emergency Supplier Fallback" candidate (7-day lead, 0.60 reliability,
1.5× cost) so the pipeline never crashes.

**Q: What if the LLM (Groq) is unavailable?**
`llm_make_decision` returns None; the DecisionAgent falls back to the prompt-tuned TOPSIS
winner. Same for Gemini in the intent router (regex fallback) and Groq in the explanation
agent (falls back gracefully). The whole system degrades to fully deterministic offline mode.

**Q: How do you handle partial stock (can't fill the full order)?**
`fulfilled_qty = min(requested_qty, available_qty)`. A partial fill keeps the candidate but
its reliability is multiplied by the fill ratio, so a full-fill option ranks higher.

---

## 8. Hackathon-Specific "Why did you build it this way?"

**Q: Why multi-agent rather than a monolith?**
Separation of concerns maps to a real supply chain: demand sensing, sourcing, ranking,
decision, and explanation are distinct roles that can evolve independently and be
traced/audited individually.

**Q: Why keep a deterministic TOPSIS core instead of letting the LLM just pick?**
The LLM sits at the language edges (intent parsing, explanation, final tie-break), while
the ranking math stays deterministic and reproducible. This is deliberate: you can always
explain *why* an option won from the weights and scores.

**Q: What's the most impressive engineering detail to highlight?**
The `DecisionAgent` — it re-reads the customer's own natural language and makes the *final*
call on top of TOPSIS, applying hard constraints (budget, price, deadline) and re-weighting
priority. It's the difference between "a formula ranked options" and "the system understood
what the customer actually asked for and decided accordingly."

**Q: What would you improve next?**
- Persist order state across restarts (currently in-memory `_orders` dict).
- Make TOPSIS use `total_cost` (not unit cost) so shipping distance factors in.
- Introduce stock scarcity / decouple reliability from proximity so different intents
genuinely diverge in the default scenario.
- Async event bus (currently synchronous pub/sub).
