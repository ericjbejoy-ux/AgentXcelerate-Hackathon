def run_topsis_optimization(candidates: list, weights: dict) -> list:
    if not candidates:
        return []
    scored_candidates = []
    for candidate in candidates:
        candidate_copy = dict(candidate)
        cost = candidate_copy.get("unit_cost", 100)
        lead_time = candidate_copy.get("lead_time_days", 5)
        reliability = candidate_copy.get("reliability_score", 0.9)
        score = (reliability * 0.4) + ((1 / (lead_time + 1)) * 0.3) + ((1 / (cost + 1)) * 0.3)
        candidate_copy["topsis_score"] = round(score, 4)
        scored_candidates.append(candidate_copy)
    return sorted(scored_candidates, key=lambda x: x["topsis_score"], reverse=True)
