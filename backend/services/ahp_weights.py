"""
Analytic Hierarchy Process (AHP) Weight Derivation Service (Saaty 1980)

Replaces hand-picked constant weights with mathematically rigorous, 
eigenvector-derived weights calibrated to petroleum geomechanics criteria.
"""

from typing import List, Dict, Any
import numpy as np


def derive_ahp_weights(pairwise_matrix: List[List[float]], criteria_names: List[str]) -> Dict[str, Any]:
    """
    Derives weights from a pairwise comparison matrix using the
    principal eigenvector method (Saaty 1980).
    pairwise_matrix[i][j] = how much more important criterion i is vs criterion j
    (Saaty scale 1-9, reciprocal for the inverse comparison).
    """
    matrix = np.array(pairwise_matrix, dtype=float)
    eigenvalues, eigenvectors = np.linalg.eig(matrix)
    max_idx = np.argmax(eigenvalues.real)
    principal_eigenvector = eigenvectors[:, max_idx].real
    
    # Ensure positive direction for eigenvector
    if np.all(principal_eigenvector < 0):
        principal_eigenvector = -principal_eigenvector
        
    weights = principal_eigenvector / principal_eigenvector.sum()

    # Consistency ratio check (Saaty's method) - warn if matrix is inconsistent
    n = len(criteria_names)
    lambda_max = float(eigenvalues[max_idx].real)
    ci = (lambda_max - n) / (n - 1) if n > 1 else 0.0
    random_index = {1: 0.0, 2: 0.0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41}.get(n, 1.45)
    cr = ci / random_index if random_index > 0 else 0.0

    return {
        "weights": {name: float(w) for name, w in zip(criteria_names, weights)},
        "consistency_ratio": float(cr),
        "consistent": cr < 0.10,  # Saaty's threshold for acceptable consistency
        "lambda_max": float(lambda_max),
        "consistency_index": float(ci),
        "random_index": float(random_index),
        "criteria": criteria_names,
        "pairwise_matrix": pairwise_matrix
    }


# ---------------------------------------------------------------------------
# DOMAIN PAIRWISE COMPARISON MATRIX (Petroleum Hazard Geomechanics)
# ---------------------------------------------------------------------------
# Criteria list:
# 1. formation_match: Stratigraphic & lithological equivalence (Barail, Tipam, Kopili)
# 2. depth_proximity: True Vertical Depth (TVD) envelope & overburden stress state
# 3. event_type_match: Structured historical hazard family (stuck pipe, kick, losses)
# 4. bm25: Lexical term frequency overlap in DDR incident logs
# 5. vector: Dense semantic embedding cosine similarity
#
# DOMAIN JUSTIFICATIONS (Saaty Scale 1-9):
# - vector is the PRIMARY signal for free-text search relevance, since it captures semantic meaning.
# - vector vs formation_match (4.0): Semantic relevance strongly outweighs pure formation overlap in free text queries.
# - vector vs depth_proximity (4.0): Semantic relevance strongly outweighs depth proximity.
# - vector vs event_type_match (3.0): Semantic relevance moderately outweighs broad event category matching.
# - vector vs bm25 (3.0): Dense semantic representations are moderately more relevant than sparse lexical term matching.
# - event_type_match and bm25 (1.0): Both provide secondary validation and are equally important.
# - formation_match and depth_proximity (1.0): Co-equal but tertiary signals for free text queries unless explicitly provided.
# ---------------------------------------------------------------------------

RETRIEVAL_CRITERIA: List[str] = [
    "formation_match",
    "depth_proximity",
    "event_type_match",
    "bm25",
    "vector"
]

RETRIEVAL_PAIRWISE_MATRIX: List[List[float]] = [
    [1.0, 1.0, 0.5, 0.5, 1/4.0],  # formation_match
    [1.0, 1.0, 0.5, 0.5, 1/4.0],  # depth_proximity
    [2.0, 2.0, 1.0, 1.0, 1/3.0],  # event_type_match
    [2.0, 2.0, 1.0, 1.0, 1/3.0],  # bm25
    [4.0, 4.0, 3.0, 3.0, 1.0],    # vector
]

# Compute at module load time
AHP_RETRIEVAL_RESULT = derive_ahp_weights(RETRIEVAL_PAIRWISE_MATRIX, RETRIEVAL_CRITERIA)
AHP_WEIGHTS: Dict[str, float] = AHP_RETRIEVAL_RESULT["weights"]
AHP_CONSISTENCY_RATIO: float = AHP_RETRIEVAL_RESULT["consistency_ratio"]
AHP_IS_CONSISTENT: bool = AHP_RETRIEVAL_RESULT["consistent"]


def get_retrieval_ahp_weights() -> Dict[str, Any]:
    """Returns the full AHP calculation payload for API and testing."""
    return AHP_RETRIEVAL_RESULT

