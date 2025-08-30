import os
import pickle
from typing import List, Tuple

import numpy as np

try:
    import faiss  # type: ignore
    _FAISS_AVAILABLE = True
except Exception:
    faiss = None  # type: ignore
    _FAISS_AVAILABLE = False


class FAISSStore:
    def __init__(self, index_path: str) -> None:
        self.index_path = index_path
        self.meta_path = f"{index_path}.meta.pkl"
        self.index = None  # type: ignore
        self.metadatas: List[Tuple[str, int]] = []

    def load(self) -> None:
        if _FAISS_AVAILABLE and os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
        if os.path.exists(self.meta_path):
            with open(self.meta_path, "rb") as f:
                self.metadatas = pickle.load(f)

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        if _FAISS_AVAILABLE and self.index is not None:
            faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "wb") as f:
            pickle.dump(self.metadatas, f)

    def add(self, embeddings: List[List[float]], metadatas: List[Tuple[str, int]]) -> None:
        vecs = np.array(embeddings).astype("float32")
        if _FAISS_AVAILABLE:
            if self.index is None:
                self.index = faiss.IndexFlatIP(vecs.shape[1])
            self.index.add(vecs)
        else:
            # store raw vectors for numpy search fallback
            # persist as .npy alongside meta
            np.save(self.index_path + ".fallback.npy", vecs)
        self.metadatas.extend(metadatas)

    def search(self, query_embedding: List[float], k: int = 5) -> List[Tuple[Tuple[str, int], float]]:
        q = np.array([query_embedding]).astype("float32")
        results: List[Tuple[Tuple[str, int], float]] = []
        if _FAISS_AVAILABLE and self.index is not None:
            scores, idxs = self.index.search(q, k)
            for i, score in zip(idxs[0], scores[0]):
                if i == -1:
                    continue
                results.append((self.metadatas[i], float(score)))
            return results

        # numpy cosine similarity fallback
        vecs_path = self.index_path + ".fallback.npy"
        if not os.path.exists(vecs_path):
            return []
        vecs = np.load(vecs_path)
        # normalize
        qn = q / (np.linalg.norm(q, axis=1, keepdims=True) + 1e-10)
        vn = vecs / (np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-10)
        sims = (vn @ qn.T).reshape(-1)
        topk = np.argsort(-sims)[:k]
        for i in topk:
            results.append((self.metadatas[int(i)], float(sims[int(i)])))
        return results

