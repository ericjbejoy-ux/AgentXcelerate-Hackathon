
import math

def run_topsis_optimization(candidates: list, weights: dict = None) -> list:
    if not candidates:
        return []

    if weights is None:
        weights = {"cost": 0.2, "lead_time": 0.4, "reliability": 0.3, "distance": 0.1}

    # Format candidate scoring
    scored_candidates = []
    for item in candidates:
        cost = item.get("unit_cost", 100)
        lead_time = item.get("lead_time_days", 5)
        reliability = item.get("reliability_score", 0.8)
        distance = item.get("distance", 100)

        # Basic weighted TOPSIS proxy score
        score = (
            (1.0 / (cost + 1e-5)) * weights.get("cost", 0.2) +
            (1.0 / (lead_time + 1e-5)) * weights.get("lead_time", 0.4) +
            (reliability) * weights.get("reliability", 0.3) +
            (1.0 / (distance + 1e-5)) * weights.get("distance", 0.1)
        )

        candidate_copy = dict(item)
        candidate_copy["topsis_score"] = round(score, 4)
        scored_candidates.append(candidate_copy)

    # Sort descending by calculated score
    scored_candidates.sort(key=lambda x: x["topsis_score"], reverse=True)
    return scored_candidates

