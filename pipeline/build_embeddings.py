"""Build optional local embedding index into data/build/embeddings.npz."""

from __future__ import annotations

import os
from pathlib import Path

from muhaqqiq.db import connect, init_db
from muhaqqiq.embeddings import DEFAULT_INDEX, DIM, hash_embed


def main() -> None:
    try:
        import numpy as np
    except ImportError as e:
        raise SystemExit("numpy required: uv sync --group embeddings") from e

    out = Path(os.environ.get("MUHAQQIQ_EMBED_INDEX", DEFAULT_INDEX))
    out.parent.mkdir(parents=True, exist_ok=True)

    conn = init_db(connect())
    kinds: list[str] = []
    ids: list[int] = []
    texts: list[str] = []

    for r in conn.execute("SELECT id, norm_skeleton FROM quran_verses"):
        kinds.append("quran")
        ids.append(int(r["id"]))
        texts.append(r["norm_skeleton"])

    for r in conn.execute("SELECT id, norm_skeleton FROM known_claims"):
        kinds.append("known_claim")
        ids.append(int(r["id"]))
        texts.append(r["norm_skeleton"])

    # Cap hadith rows for a lean default index (override with MUHAQQIQ_EMBED_HADITH_LIMIT)
    hadith_limit = int(os.environ.get("MUHAQQIQ_EMBED_HADITH_LIMIT", "4000"))
    for r in conn.execute(
        "SELECT id, norm_skeleton FROM hadiths ORDER BY length(norm_skeleton) LIMIT ?",
        (hadith_limit,),
    ):
        kinds.append("hadith")
        ids.append(int(r["id"]))
        texts.append(r["norm_skeleton"])

    conn.close()

    model = os.environ.get("MUHAQQIQ_EMBED_MODEL", "").strip()
    if model:
        from sentence_transformers import SentenceTransformer

        st = SentenceTransformer(model)
        vectors = st.encode(texts, normalize_embeddings=True, show_progress_bar=True)
        vectors = np.asarray(vectors, dtype="float32")
    else:
        vectors = np.asarray([hash_embed(t, DIM) for t in texts], dtype="float32")

    np.savez_compressed(
        out,
        vectors=vectors,
        kinds=np.asarray(kinds),
        ids=np.asarray(ids, dtype=np.int64),
    )
    print(f"Wrote {out} rows={len(ids)} dim={vectors.shape[1]} backend={'st' if model else 'hashing'}")
    print("Enable with: MUHAQQIQ_EMBEDDINGS=1")


if __name__ == "__main__":
    main()
