"""Original aggregation functions; only local error/require helpers adapted."""
import numpy as np

def require(condition, category, message):
    if not condition: raise ValueError(f"[{category}] {message}")

def unit(value: np.ndarray) -> np.ndarray:
    value = np.asarray(value, dtype=np.float64)
    norm = np.linalg.norm(value)
    require(np.isfinite(value).all() and norm > 1e-8, 'unstable_centroid', f'Invalid/near-zero centroid norm: {norm}')
    return (value / norm).astype(np.float32)

def describe(vectors: np.ndarray, weights: np.ndarray | None = None) -> dict:
    v = np.asarray(vectors, dtype=np.float64)
    require(v.ndim == 2 and len(v) > 0 and np.isfinite(v).all(), 'vectors', 'Invalid vector matrix')
    require(np.allclose(np.linalg.norm(v, axis=1), 1, atol=1e-4), 'vectors', 'Rows must be normalized')
    w = np.ones(len(v)) if weights is None else np.asarray(weights, dtype=np.float64)
    require(w.shape == (len(v),) and np.isfinite(w).all() and np.all(w > 0), 'weights', 'Invalid weights')
    average = np.average(v, axis=0, weights=w)
    centroid = unit(average)
    # Weighted sum of cosine distances: algebraically equivalent to a full N x N
    # distance matrix, without allocating it. Tie-breaking is stable first index.
    costs = 1 - v @ average
    medoid = int(np.argmin(costs))
    distances = 1 - v @ centroid
    return {'centroid': centroid, 'medoid': v[medoid].astype(np.float32), 'medoid_index': medoid,
            'raw_centroid_norm': float(np.linalg.norm(average)), 'dispersion': float(np.average(distances, weights=w)),
            'outlier_indices': np.argsort(-distances, kind='stable')[:min(3, len(v))].tolist(),
            'cosine_distance_to_centroid': distances.tolist()}

def validate_vector(vector: np.ndarray) -> None:
    require(vector.shape==(1024,) and np.isfinite(vector).all() and abs(float(np.linalg.norm(vector))-1)<1e-4,
            'vectors','Expected finite normalized 1024D dense vector')

def chapter_descriptor(vectors: np.ndarray,weights: np.ndarray) -> tuple[np.ndarray,dict]:
    for v in vectors:validate_vector(v)
    stats=describe(vectors,weights)
    # Preserve the authoritative native vector bit for bit for a single-window chapter.
    vector=vectors[0].copy() if len(vectors)==1 else stats['centroid']
    validate_vector(vector)
    return vector,{k:v for k,v in stats.items() if k not in {'centroid','medoid'}}
