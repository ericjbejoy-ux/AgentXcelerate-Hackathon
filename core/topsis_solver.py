import numpy as np

def run_topsis_optimization(candidates: list, weights: dict) -> list:
    if not candidates:
        return []

    # Criteria matrix: [cost, lead_time, reliability, distance]
    matrix = np.array([
        [
            c.get("unit_cost", 0),
            c.get("lead_time_days", 0),
            c.get("reliability_score", 0),
            c.get("distance_km", 0)
        ]
        for c in candidates
    ], dtype=float)

    # Vector Normalization
    norm_factors = np.linalg.norm(matrix, axis=0)
    norm_factors[norm_factors == 0] = 1.0
    normalized_matrix = matrix / norm_factors

    # Apply Weights
    w = np.array([
        weights.get("cost", 0.3),
        weights.get("lead_time", 0.3),
        weights.get("reliability", 0.3),
        weights.get("distance", 0.1)
    ])
    weighted_matrix = normalized_matrix * w

    # Ideal (Best) and Anti-Ideal (Worst) Solutions
    ideal_best = np.array([
        np.min(weighted_matrix[:, 0]),
        np.min(weighted_matrix[:, 1]),
        np.max(weighted_matrix[:, 2]),
        np.min(weighted_matrix[:, 3])
    ])
    
    ideal_worst = np.array([
        np.max(weighted_matrix[:, 0]),
        np.max(weighted_matrix[:, 1]),
        np.min(weighted_matrix[:, 2]),
        np.max(weighted_matrix[:, 3])
    ])

    # Euclidean Distances
    distance_best = np.sqrt(np.sum((weighted_matrix - ideal_best) ** 2, axis=1))
    distance_worst = np.sqrt(np.sum((weighted_matrix - ideal_worst) ** 2, axis=1))

    # Relative Closeness Score
    scores = distance_worst / (distance_best + distance_worst + 1e-10)

    # Attach score to candidate dicts
    scored_candidates = []
    for idx, cand in enumerate(candidates):
        item = dict(cand)
        item["topsis_score"] = round(float(scores[idx]), 4)
        scored_candidates.append(item)

    return sorted(scored_candidates, key=lambda x: x["topsis_score"], reverse=True)