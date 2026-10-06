"""Optional embedding retrieval (Phase 2.2 stage 4 / Phase 3).

Enable with MUHAQQIQ_EMBEDDINGS=1 after building an index:

    uv run python -m pipeline.build_embeddings

Backends:
  - hashing (default): char n-gram hashing, no extra ML deps beyond numpy
  - sentence-transformers: if MUHAQQIQ_EMBED_MODEL is set and package installed
"""

from __future__ import annotations

import logging
import os
import struct
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("muhaqqiq.embeddings")

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INDEX = ROOT / "data" / "build" / "embeddings.npz"
DIM = 384


@dataclass(frozen=True)
class EmbeddingHit:
    kind: str  # quran | hadith | known_claim
    id: int
    score: float  # cosine similarity 0..1


def _enabled() -> bool:
    return os.environ.get("MUHAQQIQ_EMBEDDINGS", "").strip().lower() in {"1", "true", "yes"}


def hash_embed(text: str, dim: int = DIM) -> list[float]:
    """Signed hashing trick over character 3-grams + whitespace tokens."""
    import hashlib
    import math

    vec = [0.0] * dim
    t = (text or "").strip()
    if not t:
        return vec
    grams = [t[i : i + 3] for i in range(max(0, len(t) - 2))]
    grams.extend(t.split())
    for g in grams:
        h = hashlib.blake2b(g.encode("utf-8"), digest_size=8).digest()
        idx = struct.unpack("<Q", h)[0] % dim
        sign = 1.0 if h[0] & 1 else -1.0
        vec[idx] += sign
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


class EmbeddingIndex:
    def __init__(self) -> None:
        self._kinds: list[str] = []
        self._ids: list[int] = []
        self._matrix = None  # numpy ndarray
        self._loaded = False

    def enabled(self) -> bool:
        return _enabled()

    def load(self, path: Path | None = None) -> bool:
        path = path or Path(os.environ.get("MUHAQQIQ_EMBED_INDEX", DEFAULT_INDEX))
        if not path.exists():
            logger.warning("embeddings enabled but index missing: %s", path)
            return False
        try:
            import numpy as np
        except ImportError:
            logger.warning("numpy required for embeddings; uv sync --group embeddings")
            return False
        data = np.load(path, allow_pickle=False)
        self._matrix = data["vectors"].astype("float32")
        self._kinds = [k.decode("utf-8") if isinstance(k, bytes) else str(k) for k in data["kinds"]]
        self._ids = [int(x) for x in data["ids"]]
        self._loaded = True
        logger.info("Loaded embedding index %s (%d rows)", path, len(self._ids))
        return True

    def encode(self, text: str):
        import numpy as np

        model = os.environ.get("MUHAQQIQ_EMBED_MODEL", "").strip()
        if model:
            try:
                from sentence_transformers import SentenceTransformer

                st = getattr(self, "_st", None)
                if st is None:
                    self._st = SentenceTransformer(model)
                    st = self._st
                v = st.encode([text], normalize_embeddings=True)[0]
                return np.asarray(v, dtype="float32")
            except Exception as exc:  # noqa: BLE001
                logger.debug("sentence-transformers failed, falling back to hashing: %s", exc)
        return np.asarray(hash_embed(text), dtype="float32")

    def query(self, text: str, *, top_k: int = 20) -> list[EmbeddingHit]:
        if not self.enabled():
            return []
        if not self._loaded and not self.load():
            return []
        import numpy as np

        assert self._matrix is not None
        q = self.encode(text)
        if q.shape[0] != self._matrix.shape[1]:
            # Rebuild mismatch — skip rather than crash matcher
            logger.warning(
                "embedding dim mismatch query=%s index=%s", q.shape[0], self._matrix.shape[1]
            )
            return []
        scores = self._matrix @ q
        if top_k >= len(scores):
            idxs = np.argsort(-scores)
        else:
            idxs = np.argpartition(-scores, top_k)[:top_k]
            idxs = idxs[np.argsort(-scores[idxs])]
        out: list[EmbeddingHit] = []
        for i in idxs[:top_k]:
            s = float(scores[i])
            if s < 0.35:
                continue
            out.append(EmbeddingHit(kind=self._kinds[i], id=self._ids[i], score=s))
        return out


DEFAULT_EMBEDDINGS = EmbeddingIndex()
