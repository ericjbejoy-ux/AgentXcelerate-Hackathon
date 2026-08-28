# AgentXcelerate: Autonomous Supply Chain Ops
## 3-Minute Hackathon Presentation

### Problem Statement
Traditional supply chain management suffers from:
- Manual order processing causing delays
- Poor inventory visibility across warehouses
- Inefficient supplier selection
- Lack of real-time decision-making
- Suboptimal trade-offs between cost, speed, and reliability

### Solution Approach
We built an **event-driven multi-agent autonomous system** that:
1. **Parses user intent** from natural language notes (e.g., "need it within 3 days", "cheapest option")
2. **Generates candidates** by scanning warehouse inventory + querying external suppliers
3. **Applies geospatial routing** to adjust lead times based on actual distance from user location
4. **Ranks options** using TOPSIS multi-criteria optimization (cost, lead time, reliability)
5. **Explains decisions** via LLM-generated plain-English reasoning
6. **Learns from feedback** - rejection reasons improve future recommendations

### Key Technologies
- **Backend**: Python/FastAPI, SQLite, TOPSIS algorithm
- **AI/ML**: Groq LLM (Qwen 3.8B) for explanations, Nominatim/OpenStreetMap for geocoding
- **Frontend**: React/Vite, Tailwind CSS, modern UI/UX with Operate-surface design
- **Architecture**: Async orchestrator + event bus + specialized agents (Demand, Geo, Decision, Explanation)

### Innovation Highlights
- **Intent-driven prioritization**: Dynamically adjusts decision weights based on user language
- **Geospatial awareness**: Real distance calculations for accurate lead-time estimates
- **Feedback loop**: User rejection reasons directly influence LLM re-ranking prompts
- **Multi-modal sourcing**: Simultaneously considers internal warehouse stock and external suppliers
- **Explainable AI**: Every recommendation includes human-readable justification

### Demo Flow
1. User submits order: "HYD-1001, qty 10, need it within 3 days"
2. System scans 15 warehouses + 3 suppliers → generates 18 candidates
3. Applies distance adjustments from user location (Mumbai)
4. TOPSIS ranks by cost/speed/reliability weights (intent-derived)
5. LLM explains: "Selected Mumbai West Hub for fastest delivery (1-day lead)"
6. User rejects: "too expensive" → system remembers reason
7. Re-ranking excludes expensive option → shows next-best: Nagpur Central (cheaper, 5-day lead)
8. User approves → order executes against selected inventory/supplier

### Impact
- Reduces decision time from hours/minutes to seconds
- Improves inventory utilization through intelligent sourcing
- Increases user satisfaction via transparent, adaptive recommendations
- Demonstrates practical autonomous agent coordination in logistics

**Built for AgentXcelerate Hackathon - Transforming supply chain ops with AI agents**