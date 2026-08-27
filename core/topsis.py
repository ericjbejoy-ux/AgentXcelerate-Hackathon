import logging
import numpy as np

logger = logging.getLogger("topsis")


def run_topsis_optimization(candidates: list, weights: dict) -> list:
    logger.info("[TOPSIS] RECEIVED %d candidates from DemandAgent", len(candidates))
    for i, c in enumerate(candidates):
        logger.info("[TOPSIS]   CANDIDATE %d: %s — cost=$%.2f, lead=%dd, reliability=%.2f",
                     i+1, c.get("strategy_name", "?"), c.get("unit_cost", 0),
                     c.get("lead_time_days", 0), c.get("reliability_score", 0))

    if not candidates:
        logger.warning("[TOPSIS] No candidates to rank")
        return []

    if len(candidates) == 1:
        c = dict(candidates[0])
        c["topsis_score"] = 1.0
        logger.info("[TOPSIS] Single candidate — score=1.0")
        return [c]

    w_cost = weights.get("cost", 0.33)
    w_lead = weights.get("lead_time", 0.33)
    w_rel = weights.get("reliability", 0.34)
    logger.info("[TOPSIS] WEIGHTS: cost=%.2f, lead_time=%.2f, reliability=%.2f", w_cost, w_lead, w_rel)

    matrix = []
    for c in candidates:
        matrix.append([
            c.get("unit_cost", 100.0),
            c.get("lead_time_days", 5),
            c.get("reliability_score", 0.9),
        ])

    mat = np.array(matrix, dtype=float)
    logger.info("[TOPSIS] DECISION MATRIX:\n%s", mat)

    norms = np.sqrt((mat ** 2).sum(axis=0))
    norms[norms == 0] = 1.0
    norm_mat = mat / norms

    ideal_best = np.array([norm_mat[:, 0].min(), norm_mat[:, 1].min(), norm_mat[:, 2].max()])
    ideal_worst = np.array([norm_mat[:, 0].max(), norm_mat[:, 1].max(), norm_mat[:, 2].min()])
    logger.info("[TOPSIS] IDEAL BEST:  [cost=%.4f, lead=%.4f, rel=%.4f]", *ideal_best)
    logger.info("[TOPSIS] IDEAL WORST: [cost=%.4f, lead=%.4f, rel=%.4f]", *ideal_worst)

    weights_arr = np.array([w_cost, w_lead, w_rel])
    weighted = norm_mat * weights_arr

    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    denom = dist_best + dist_worst
    denom[denom == 0] = 1.0
    scores = dist_worst / denom

    scored = []
    for i, c in enumerate(candidates):
        entry = dict(c)
        entry["topsis_score"] = round(float(scores[i]), 4)
        scored.append(entry)

    ranked = sorted(scored, key=lambda x: x["topsis_score"], reverse=True)
    logger.info("[TOPSIS] RANKED RESULTS:")
    for i, r in enumerate(ranked):
        logger.info("[TOPSIS]   #%d: %s — score=%.4f (cost=$%.2f, lead=%dd, rel=%.2f)",
                     i+1, r.get("strategy_name"), r["topsis_score"],
                     r.get("unit_cost", 0), r.get("lead_time_days", 0), r.get("reliability_score", 0))
    logger.info("[TOPSIS] WINNER: %s (score=%.4f)", ranked[0]["strategy_name"], ranked[0]["topsis_score"])

    return ranked
