import numpy as np

def calculate_topsis(matrix: np.ndarray, weights: np.ndarray, impacts: np.ndarray) -> np.ndarray:
    """
    Calculates TOPSIS relative closeness scores.
    matrix: 2D array [options x criteria] -> [Lead Time, Total Cost, Priority Impact]
    impacts: 1 for maximize, -1 for minimize -> [-1, -1, 1]
    """
    norm_matrix = matrix / np.sqrt((matrix**2).sum(axis=0))
    weighted_matrix = norm_matrix * weights
    
    ideal_best = np.where(impacts == 1, weighted_matrix.max(axis=0), weighted_matrix.min(axis=0))
    ideal_worst = np.where(impacts == 1, weighted_matrix.min(axis=0), weighted_matrix.max(axis=0))
    
    dist_best = np.sqrt(((weighted_matrix - ideal_best)**2).sum(axis=1))
    dist_worst = np.sqrt(((weighted_matrix - ideal_worst)**2).sum(axis=1))
    
    scores = dist_worst / (dist_best + dist_worst)
    # Handle single-row edge case where both distances are zero
    scores = np.nan_to_num(scores, nan=1.0)
    return scores
