"""Retrieval stages: exact → FTS/trigram → RapidFuzz → optional embeddings."""

from __future__ import annotations

import sqlite3
from typing import Any

from rapidfuzz import fuzz

from muhaqqiq.domain.decide import M_MIN, T_CLOSE, T_EXACT, Candidate, decide
from muhaqqiq.domain.diff import char_diff, diff_highlight, user_diff_highlight
from muhaqqiq.domain.normalize import normalize, word_count
from muhaqqiq.domain.segment import segment
from muhaqqiq.repositories.embeddings import DEFAULT_EMBEDDINGS
from muhaqqiq.repositories.retrieval_pg import trigram_shortlist

MIN_FUZZY_CANDIDATE_CHARS = 6
MIN_CONTAINMENT_QUERY_CHARS = 10
# Query much shorter than source: require contiguous evidence (no bag-of-words wins)
SHORT_QUERY_LEN_RATIO = 0.35
MIN_PARTIAL_COVERAGE = 0.85


def _tokens_in_order(query: str, window: str) -> bool:
    """True if query tokens appear in order inside window (allowing gaps of 1 token)."""
    q_toks = [t for t in query.split() if t]
    w_toks = [t for t in window.split() if t]
    if not q_toks:
        return False
    if len(q_toks) == 1:
        return q_toks[0] in w_toks
    # Allow a small window expansion for one skipped token between matches
    max_span = len(q_toks) + 1
    for start in range(len(w_toks)):
        i = 0
        for j in range(start, min(start + max_span, len(w_toks))):
            if w_toks[j] == q_toks[i]:
                i += 1
                if i == len(q_toks):
                    return True
        if i == len(q_toks):
            return True
    return False


def _best_alignment_span(query: str, candidate: str) -> tuple[float, str]:
    """Return (partial_ratio score, aligned candidate substring).

    RapidFuzz ScoreAlignment: src_* indexes s1 (query), dest_* indexes s2 (candidate).
    """
    if not query or not candidate:
        return 0.0, ""
    try:
        aln = fuzz.partial_ratio_alignment(query, candidate)
    except Exception:
        return float(fuzz.partial_ratio(query, candidate)), ""
    if aln is None:
        return 0.0, ""
    span = candidate[aln.dest_start : aln.dest_end]
    return float(aln.score), span


def _matched_display_span(query_norm: str, candidate_norm: str, display: str) -> str | None:
    """Map best normalized alignment window onto display text (best-effort)."""
    if not query_norm or not candidate_norm or not display:
        return None
    score, span = _best_alignment_span(query_norm, candidate_norm)
    if score < T_CLOSE or not span:
        return None
    d_words = display.split()
    s_words = span.split()
    if not d_words or not s_words:
        return span
    best_i, best_s = 0, -1.0
    win = max(len(s_words), 1)
    for i in range(0, max(len(d_words) - win + 1, 1)):
        chunk = " ".join(d_words[i : i + win + 2])
        sc = float(fuzz.partial_ratio(span, normalize(chunk)))
        if sc > best_s:
            best_s = sc
            best_i = i
    if best_s < 60:
        return span
    end = min(len(d_words), best_i + win + 2)
    return " ".join(d_words[best_i:end])


def _query_coverage(query: str, candidate: str) -> float:
    """Fraction of query quality explained by the best contiguous candidate window."""
    if not query or not candidate:
        return 0.0
    if query in candidate:
        return 1.0
    score, span = _best_alignment_span(query, candidate)
    if not span:
        return score / 100.0
    # Contiguous window must also keep query tokens in order
    if word_count(query) >= 2 and not _tokens_in_order(query, span) and query not in candidate:
        return min(score / 100.0, 0.5)
    return score / 100.0


def _score(query: str, candidate: str) -> float:
    if not query or not candidate:
        return 0.0
    if query == candidate:
        return 100.0

    # Partial quote inside a longer source (hadith with isnad).
    # Require multi-word queries — a single common token is not a quote.
    if (
        word_count(query) >= 2
        and len(query) >= MIN_CONTAINMENT_QUERY_CHARS
        and query in candidate
    ):
        return 99.0

    # Source sits inside a longer / tampered user text → CLOSE band, not Supported
    if (
        len(candidate) >= MIN_FUZZY_CANDIDATE_CHARS
        and candidate in query
        and candidate != query
    ):
        coverage = len(candidate) / max(len(query), 1)
        token = float(fuzz.token_set_ratio(query, candidate))
        # High coverage nearly-only-this-verse → near exact; else Close
        if coverage >= 0.92:
            return max(93.0, token)
        return max(T_CLOSE, min(91.0, max(float(fuzz.ratio(query, candidate)), token * 0.92)))

    # Short sources must not win via partial_ratio against long queries
    if len(candidate) < max(MIN_FUZZY_CANDIDATE_CHARS, int(len(query) * 0.45)):
        return float(fuzz.ratio(query, candidate))

    len_ratio = len(query) / max(len(candidate), 1)
    q_words = word_count(query)
    ratio = float(fuzz.ratio(query, candidate))

    # Tiny queries: substring presence is not a quote (blocks نبي/لا/حديث → full ayah)
    if q_words < 4 and len(query) < MIN_CONTAINMENT_QUERY_CHARS:
        return ratio

    # Short/partial quote vs longer source (e.g. matn inside isnad): no token_set wins
    if len_ratio < SHORT_QUERY_LEN_RATIO or q_words < 4:
        partial, span = _best_alignment_span(query, candidate)
        # Strict contiguous coverage only for short queries (blocks scattered vocab)
        if q_words < 4:
            coverage = _query_coverage(query, candidate)
            if coverage < MIN_PARTIAL_COVERAGE:
                return ratio
            if span and not _tokens_in_order(query, span) and query not in candidate:
                return ratio
            return float(max(ratio, partial))
        # Longer queries inside long haystacks: require strong partial (not weak boilerplate)
        if partial < 80.0:
            return ratio
        return float(max(ratio, partial))

    partial = float(fuzz.partial_ratio(query, candidate))
    tsr = float(fuzz.token_set_ratio(query, candidate))
    # token_set can be 100 when query tokens ⊆ candidate (deleted-word false Supported).
    # Only trust it when lengths are close; otherwise small corroborating boost.
    if tsr > max(ratio, partial) and len_ratio < 0.85:
        tsr = min(tsr, max(ratio, partial) + 5.0)
    best = float(max(ratio, partial, tsr))
    # Weak partial-only hits (shared stopwords) must not enter Close band
    if best == partial and partial < 80.0 and ratio < T_CLOSE:
        return ratio
    return best


def _quran_candidate(r: sqlite3.Row, score: float, *, exact: bool = False, norm: str | None = None,
                     display: str | None = None, ref_extra: dict | None = None) -> Candidate:
    ref = {"sura": r["sura"], "aya": r["aya"], "source": "Tanzil"}
    if ref_extra:
        ref.update(ref_extra)
    return Candidate(
        kind="quran",
        id=r["id"],
        score=score,
        exact=exact,
        text_display=display if display is not None else r["text_uthmani"],
        norm=norm if norm is not None else r["norm_skeleton"],
        ref=ref,
    )


def _hadith_candidate(r: sqlite3.Row, score: float, *, exact: bool = False) -> Candidate:
    keys = set(r.keys()) if hasattr(r, "keys") else set()
    ref: dict[str, Any] = {
        "collection": r["collection"],
        "number": r["number"],
        "source": r["collection"],
    }
    if "enc_id" in keys and r["enc_id"]:
        ref["enc_id"] = r["enc_id"]
    if "proof_url" in keys and r["proof_url"]:
        ref["proof_url"] = r["proof_url"]
        ref["url"] = r["proof_url"]
    return Candidate(
        kind="hadith",
        id=r["id"],
        score=score,
        exact=exact,
        text_display=r["text_ar"],
        norm=r["norm_skeleton"],
        ref=ref,
    )


def _exact_quran(conn: sqlite3.Connection, skeleton: str) -> list[Candidate]:
    rows = conn.execute(
        "SELECT id, sura, aya, text_uthmani, norm_skeleton FROM quran_verses WHERE norm_skeleton = ?",
        (skeleton,),
    ).fetchall()
    return [_quran_candidate(r, 100.0, exact=True) for r in rows]


def _exact_hadith(conn: sqlite3.Connection, skeleton: str) -> list[Candidate]:
    rows = conn.execute(
        "SELECT id, collection, number, text_ar, norm_skeleton, enc_id, proof_url "
        "FROM hadiths WHERE norm_skeleton = ?",
        (skeleton,),
    ).fetchall()
    return [_hadith_candidate(r, 100.0, exact=True) for r in rows]


def _enc_hadith_candidates(conn: sqlite3.Connection, skeleton: str) -> list[Candidate]:
    try:
        rows = conn.execute(
            "SELECT id, enc_id, text_ar, norm_skeleton, attribution, grade, reference, url "
            "FROM enc_hadiths"
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    out: list[Candidate] = []
    for r in rows:
        # Full-string fidelity only — never treat short query ⊆ long Enc matn as exact
        s = float(fuzz.ratio(skeleton, r["norm_skeleton"]))
        if r["norm_skeleton"] == skeleton:
            s = 100.0
        if s < 99:
            continue
        grade = (r["grade"] or "").strip()
        grading = None
        if grade:
            grading = {
                "grader": r["attribution"] or "HadeethEnc",
                "grade": grade,
                "ruling": grade,
                "reference": r["reference"] or f"HadeethEnc #{r['enc_id']}",
                "url": r["url"],
                "source": "HadeethEnc",
            }
        out.append(
            Candidate(
                kind="enc_hadith",
                id=int(r["id"]),
                score=s,
                exact=r["norm_skeleton"] == skeleton,
                text_display=r["text_ar"],
                norm=r["norm_skeleton"],
                ref={
                    "claim_type": "hadeethenc",
                    "enc_id": r["enc_id"],
                    "url": r["url"],
                },
                has_grading=grading is not None,
                grading=grading,
            )
        )
    return out


def _claim_rulings(conn: sqlite3.Connection, claim_id: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT grader, ruling, reference, url FROM known_claim_rulings
        WHERE claim_id = ? ORDER BY id
        """,
        (claim_id,),
    ).fetchall()
    return [
        {
            "grader": r["grader"],
            "grade": r["ruling"],
            "ruling": r["ruling"],
            "reference": r["reference"],
            "url": r["url"],
            "source": "seed",
        }
        for r in rows
    ]


def _hadith_gradings(conn: sqlite3.Connection, hadith_id: int) -> list[dict[str, Any]]:
    try:
        rows = conn.execute(
            """
            SELECT grader, grade_label, reference, url FROM gradings
            WHERE hadith_id = ? ORDER BY id
            """,
            (hadith_id,),
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    return [
        {
            "grader": r["grader"],
            "grade": r["grade_label"],
            "ruling": r["grade_label"],
            "reference": r["reference"],
            "url": r["url"],
            "source": "HadeethEnc",
        }
        for r in rows
    ]


def _translations(conn: sqlite3.Connection, kind: str, ref_id: int) -> list[dict[str, str]]:
    try:
        rows = conn.execute(
            "SELECT lang, text FROM translations WHERE kind = ? AND ref_id = ? ORDER BY lang",
            (kind, ref_id),
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    return [{"lang": r["lang"], "text": r["text"]} for r in rows]


def _proof_url(kind: str, ref: dict[str, Any], *, enc_id: str | None = None) -> str | None:
    if kind == "quran" and ref.get("sura") and ref.get("aya"):
        return f"https://tanzil.net/#{ref['sura']}:{ref['aya']}"
    eid = enc_id or ref.get("enc_id")
    if eid:
        return f"https://hadeethenc.com/ar/hadeeth/{eid}"
    if kind == "hadith" and ref.get("collection") and ref.get("number"):
        return None
    if ref.get("url"):
        return str(ref["url"])
    return None


def _exact_claims(conn: sqlite3.Connection, skeleton: str) -> list[Candidate]:
    rows = conn.execute(
        """
        SELECT c.id, c.text_ar, c.norm_skeleton, c.claim_type
        FROM known_claims c
        WHERE c.norm_skeleton = ?
        """,
        (skeleton,),
    ).fetchall()
    return [_claim_candidate(conn, r, 100.0, exact=True) for r in rows]


def _claim_candidate(
    conn: sqlite3.Connection, r: sqlite3.Row, score: float, *, exact: bool
) -> Candidate:
    rulings = _claim_rulings(conn, int(r["id"]))
    grading = rulings[0] if rulings else None
    return Candidate(
        kind="known_claim",
        id=r["id"],
        score=score,
        exact=exact,
        text_display=r["text_ar"],
        norm=r["norm_skeleton"],
        ref={"claim_type": r["claim_type"], "url": (grading or {}).get("url")},
        has_grading=bool(rulings),
        grading=grading,
    )


# High-frequency tokens flood FTS OR queries and crowd out distinctive stems.
_FTS_STOP = {
    "الله",
    "من",
    "ما",
    "لا",
    "في",
    "علي",
    "الي",
    "ان",
    "انما",
    "هذا",
    "هذه",
    "ذلك",
    "التي",
    "الذي",
    "كان",
    "قد",
    "عن",
    "مع",
    "كل",
}


def _fts_ids(conn: sqlite3.Connection, table: str, id_col: str, skeleton: str, limit: int = 100) -> list[int]:
    tokens = [t for t in skeleton.split() if len(t) >= 2]
    if not tokens:
        return []
    n_words = len(tokens)
    content = [t for t in tokens if t not in _FTS_STOP and len(t) >= 3]
    # Prefer longer/rarer stems; fall back to all tokens if too few content words.
    ranked = sorted(content or tokens, key=len, reverse=True)[:10]
    queries: list[str] = []
    if len(content) >= 3:
        # AND keeps multi-word Quran/hadith pastes from drowning in الله/ما hits.
        queries.append(" AND ".join(f'"{t}"' for t in ranked[:6]))
    elif len(content) == 2 and n_words < 6:
        # Short distinctive pairs: require both tokens (avoid OR flood on common stems)
        queries.append(" AND ".join(f'"{t}"' for t in ranked[:2]))
    # Per-token queries surface rare stems (e.g. اشكو) even when OCR garbles neighbors.
    # Skip for very short queries dominated by stopwords — they drown recall in noise.
    if n_words >= 4 or len(content) >= 2:
        for t in ranked:
            if len(t) >= 4:
                queries.append(f'"{t}"')
    if n_words >= 4:
        queries.append(" OR ".join(f'"{t}"' for t in ranked[:8]))
    elif ranked and not queries:
        # Last resort for short inputs: single rarest content token only
        queries.append(f'"{ranked[0]}"')
    seen: list[int] = []
    got: set[int] = set()
    try:
        for q in queries:
            # contentless fts5 (content='') returns NULL for columns; rowid == verse/hadith id
            rows = conn.execute(
                f"SELECT rowid AS id FROM {table} WHERE {table} MATCH ? LIMIT ?",
                (q, limit),
            ).fetchall()
            for r in rows:
                i = int(r["id"])
                if i not in got:
                    got.add(i)
                    seen.append(i)
            if len(seen) >= limit:
                break
        return seen[:limit]
    except sqlite3.OperationalError:
        return []


def _containment_hadith(conn: sqlite3.Connection, skeleton: str) -> list[Candidate]:
    # Single tokens / tiny fragments are not quotes (e.g. خيركم ⊆ many matns).
    if word_count(skeleton) < 2 or len(skeleton) < MIN_CONTAINMENT_QUERY_CHARS:
        return []
    # Allow 2-word famous phrases if long enough (e.g. الدين النصيحة)
    if word_count(skeleton) < 3 and len(skeleton) < 12:
        return []
    rows = conn.execute(
        "SELECT id, collection, number, text_ar, norm_skeleton, enc_id, proof_url FROM hadiths "
        "WHERE norm_skeleton LIKE ? LIMIT 20",
        (f"%{skeleton}%",),
    ).fetchall()
    return [_hadith_candidate(r, 99.0) for r in rows]


def _containment_quran(conn: sqlite3.Connection, skeleton: str) -> list[Candidate]:
    if word_count(skeleton) < 2 or len(skeleton) < 6:
        return []
    rows = conn.execute(
        "SELECT id, sura, aya, text_uthmani, norm_skeleton FROM quran_verses "
        "WHERE norm_skeleton LIKE ? OR ? LIKE '%' || norm_skeleton || '%' LIMIT 40",
        (f"%{skeleton}%", skeleton),
    ).fetchall()
    out: list[Candidate] = []
    for r in rows:
        if len(r["norm_skeleton"]) < MIN_FUZZY_CANDIDATE_CHARS and r["norm_skeleton"] != skeleton:
            continue
        score = _score(skeleton, r["norm_skeleton"])
        if score < T_CLOSE:
            continue
        out.append(_quran_candidate(r, score, exact=r["norm_skeleton"] == skeleton))
    return out


def _neighbor_pairs(conn: sqlite3.Connection, skeleton: str, seed_ids: list[int]) -> list[Candidate]:
    """Score consecutive verse pairs around FTS hits (multi-verse pastes)."""
    out: list[Candidate] = []
    seen: set[tuple[int, int]] = set()
    for vid in seed_ids[:30]:
        row = conn.execute(
            "SELECT id, sura, aya, text_uthmani, norm_skeleton FROM quran_verses WHERE id = ?",
            (vid,),
        ).fetchone()
        if not row:
            continue
        neighbors = conn.execute(
            """
            SELECT id, sura, aya, text_uthmani, norm_skeleton FROM quran_verses
            WHERE sura = ? AND aya IN (?, ?, ?)
            ORDER BY aya
            """,
            (row["sura"], row["aya"] - 1, row["aya"], row["aya"] + 1),
        ).fetchall()
        for i in range(len(neighbors) - 1):
            a, b = neighbors[i], neighbors[i + 1]
            if b["aya"] != a["aya"] + 1:
                continue
            key = (a["id"], b["id"])
            if key in seen:
                continue
            seen.add(key)
            combined = f"{a['norm_skeleton']} {b['norm_skeleton']}"
            if combined == skeleton:
                score = 100.0
                exact = True
            else:
                # Prefer full-string ratio for multi-verse pastes.
                # Non-exact pairs must not enter Supported band (tamper safety).
                score = max(_score(skeleton, combined), float(fuzz.ratio(skeleton, combined)))
                if score >= T_EXACT:
                    score = T_EXACT - 0.5
                exact = False
            if score < T_CLOSE:
                continue
            display = f"{a['text_uthmani']} {b['text_uthmani']}"
            out.append(
                _quran_candidate(
                    a,
                    score,
                    exact=exact,
                    norm=combined,
                    display=display,
                    ref_extra={"aya_end": b["aya"]},
                )
            )
    return out


def _fuzzy_pool(conn: sqlite3.Connection, skeleton: str) -> list[Candidate]:
    candidates: list[Candidate] = []
    candidates.extend(_containment_hadith(conn, skeleton))
    candidates.extend(_containment_quran(conn, skeleton))

    q_ids = _fts_ids(conn, "quran_fts", "verse_id", skeleton)
    if q_ids:
        placeholders = ",".join("?" * len(q_ids))
        rows = conn.execute(
            f"SELECT id, sura, aya, text_uthmani, norm_skeleton FROM quran_verses WHERE id IN ({placeholders})",
            q_ids,
        ).fetchall()
        for r in rows:
            if len(r["norm_skeleton"]) < MIN_FUZZY_CANDIDATE_CHARS and r["norm_skeleton"] != skeleton:
                continue
            s = _score(skeleton, r["norm_skeleton"])
            if s < T_CLOSE:
                continue
            candidates.append(_quran_candidate(r, s))

    # Prefer containment / short-opener seeds first so they are not truncated
    quran_seed_ids: list[int] = []
    quran_seed_ids.extend(c.id for c in candidates if c.kind == "quran")
    for tok in skeleton.split()[:2]:
        if 2 <= len(tok) <= 3:
            for r in conn.execute(
                "SELECT id FROM quran_verses WHERE norm_skeleton = ?", (tok,)
            ):
                quran_seed_ids.append(r["id"])
    quran_seed_ids.extend(q_ids)
    seen_seed: set[int] = set()
    ordered_seeds: list[int] = []
    for vid in quran_seed_ids:
        if vid in seen_seed:
            continue
        seen_seed.add(vid)
        ordered_seeds.append(vid)
    candidates.extend(_neighbor_pairs(conn, skeleton, ordered_seeds))

    h_ids = _fts_ids(conn, "hadith_fts", "hadith_id", skeleton)
    seen_hadith: set[int] = set()
    if h_ids:
        placeholders = ",".join("?" * len(h_ids))
        hrows = conn.execute(
            f"SELECT id, collection, number, text_ar, norm_skeleton FROM hadiths WHERE id IN ({placeholders})",
            h_ids,
        ).fetchall()
        for r in hrows:
            seen_hadith.add(r["id"])
            s = _score(skeleton, r["norm_skeleton"])
            if s < T_CLOSE:
                continue
            candidates.append(_hadith_candidate(r, s))

    # Distinctive matn fragments (avoid boilerplate like "قال رسول الله")
    boilerplate = {
        "قال", "رسول", "الله", "النبي", "نبي", "صلي", "عليه", "وسلم",
        "عن", "في", "من", "علي", "ابي", "هريره", "رضي", "ان", "كان",
        "حدثنا", "اخبرنا", "قالت", "روي", "انما",
    }
    words = skeleton.split()
    if len(words) >= 3:
        for i in range(len(words) - 2):
            frag_words = words[i : i + 3]
            frag = " ".join(frag_words)
            if len(frag) < 12:
                continue
            distinctive = [w for w in frag_words if w not in boilerplate and len(w) >= 4]
            if len(distinctive) < 2:
                continue
            rows = conn.execute(
                "SELECT id, collection, number, text_ar, norm_skeleton FROM hadiths "
                "WHERE norm_skeleton LIKE ? LIMIT 15",
                (f"%{frag}%",),
            ).fetchall()
            for r in rows:
                seen_hadith.add(r["id"])
                if skeleton in r["norm_skeleton"]:
                    candidates.append(_hadith_candidate(r, 99.0))
                    continue
                # Fragment hit is for recall; score the full query honestly
                s = _score(skeleton, r["norm_skeleton"])
                # Strong matn coverage: fragment is most of the query and contiguous
                if (
                    frag in r["norm_skeleton"]
                    and skeleton in r["norm_skeleton"]
                    and len(frag) / max(len(skeleton), 1) >= 0.55
                ):
                    s = max(s, 99.0)
                if s >= T_CLOSE:
                    candidates.append(_hadith_candidate(r, s))

    # Known claims: never match via tiny query containment
    crows = conn.execute(
        "SELECT c.id, c.text_ar, c.norm_skeleton, c.claim_type FROM known_claims c"
    ).fetchall()
    for r in crows:
        if word_count(skeleton) < 3 and r["norm_skeleton"] != skeleton:
            s = float(fuzz.ratio(skeleton, r["norm_skeleton"]))
        else:
            s = _score(skeleton, r["norm_skeleton"])
        if s < 88:
            continue
        candidates.append(_claim_candidate(conn, r, s, exact=False))

    candidates.extend(_enc_hadith_candidates(conn, skeleton))

    # Stage 2 (Postgres): pg_trgm shortlist when DATABASE_URL is set
    for row in trigram_shortlist(skeleton, kind="quran", limit=50):
        if len(row["norm_skeleton"]) < MIN_FUZZY_CANDIDATE_CHARS and row["norm_skeleton"] != skeleton:
            continue
        s = _score(skeleton, row["norm_skeleton"])
        if s >= T_CLOSE:
            candidates.append(_quran_candidate(row, s))
    for row in trigram_shortlist(skeleton, kind="hadith", limit=50):
        s = _score(skeleton, row["norm_skeleton"])
        if s >= T_CLOSE:
            candidates.append(_hadith_candidate(row, s))
    for row in trigram_shortlist(skeleton, kind="known_claim", limit=20):
        s = _score(skeleton, row["norm_skeleton"])
        if s >= 88:
            candidates.append(_claim_candidate(conn, row, s, exact=False))

    # Stage 4: embeddings shortlist ids only; score via RapidFuzz (never cite from cosine alone).
    # Use full-string ratio only (no containment / partial) so emb cannot invent Supported.
    for hit in DEFAULT_EMBEDDINGS.query(skeleton, top_k=20):
        if hit.kind == "quran":
            r = conn.execute(
                "SELECT id, sura, aya, text_uthmani, norm_skeleton FROM quran_verses WHERE id = ?",
                (hit.id,),
            ).fetchone()
            if r:
                s = float(fuzz.ratio(skeleton, r["norm_skeleton"]))
                if r["norm_skeleton"] == skeleton:
                    s = 100.0
                if s >= T_CLOSE:
                    if s < 99.0:
                        s = min(s, T_EXACT - 0.5)
                    candidates.append(_quran_candidate(r, s, exact=s >= 100.0))
        elif hit.kind == "hadith":
            r = conn.execute(
                "SELECT id, collection, number, text_ar, norm_skeleton, enc_id, proof_url FROM hadiths WHERE id = ?",
                (hit.id,),
            ).fetchone()
            if r:
                s = float(fuzz.ratio(skeleton, r["norm_skeleton"]))
                if r["norm_skeleton"] == skeleton:
                    s = 100.0
                if s >= T_CLOSE:
                    if s < 99.0:
                        s = min(s, T_EXACT - 0.5)
                    candidates.append(_hadith_candidate(r, s, exact=s >= 100.0))

    candidates.sort(key=lambda c: c.score, reverse=True)
    return candidates


def _length_fit(query: str, candidate_norm: str) -> float:
    """Closer to 1.0 when query and candidate lengths match (prefer full verse over long paste)."""
    if not query or not candidate_norm:
        return 0.0
    a, b = len(query), len(candidate_norm)
    return min(a, b) / max(a, b)


def _prefer_type(ranked: list[Candidate], claim_type: str, query: str = "") -> Candidate | None:
    if not ranked:
        return None
    # Near-tied scores: prefer better length fit so a short ayah beats a long verse containing it
    top = ranked[0].score
    tied = [c for c in ranked if c.score >= top - 0.5]
    if len(tied) > 1 and query:
        tied.sort(key=lambda c: (_length_fit(query, c.norm), c.score), reverse=True)
        best = tied[0]
    else:
        best = ranked[0]
    if claim_type == "verse":
        q = next((c for c in ranked if c.kind == "quran" and c.score >= best.score - 3), None)
        if q and query:
            q_tied = [c for c in ranked if c.kind == "quran" and c.score >= q.score - 0.5]
            if len(q_tied) > 1:
                q_tied.sort(key=lambda c: (_length_fit(query, c.norm), c.score), reverse=True)
                return q_tied[0]
        return q or best
    if claim_type in {"hadith", "athar"}:
        h = next(
            (
                c
                for c in ranked
                if c.kind in {"hadith", "known_claim"} and c.score >= best.score - 3
            ),
            None,
        )
        return h or best
    return best


def _match_one(conn: sqlite3.Connection, text: str, claim_type: str = "unknown") -> dict[str, Any]:
    skeleton = normalize(text)
    n_words = word_count(skeleton)

    pool: list[Candidate] = []
    # Stage 1: exact
    pool.extend(_exact_claims(conn, skeleton))
    pool.extend(_exact_quran(conn, skeleton))
    pool.extend(_exact_hadith(conn, skeleton))

    if not any(c.exact for c in pool):
        # Stages 2–4
        pool.extend(_fuzzy_pool(conn, skeleton))

    best_by_key: dict[tuple[str, int, str], Candidate] = {}
    for c in pool:
        key = (c.kind, c.id, c.norm)
        if key not in best_by_key or c.score > best_by_key[key].score:
            best_by_key[key] = c
    ranked = sorted(best_by_key.values(), key=lambda c: c.score, reverse=True)

    # One-token queries: drop non-exact hits (common stems ⊆ many matns).
    if n_words < 2:
        ranked = [c for c in ranked if c.exact]
        best_by_key = {(c.kind, c.id, c.norm): c for c in ranked}

    best = _prefer_type(ranked, claim_type, skeleton)
    if ranked:
        known = next(
            (c for c in ranked if c.kind == "known_claim" and c.score >= 88),
            None,
        )
        if known is not None and (
            best is None or best.kind == "known_claim" or known.score >= best.score
        ):
            best = known
        # Enc grades only win when exact/near-exact and no stronger Core match
        if best is None or best.kind not in {"known_claim"}:
            enc = next(
                (
                    c
                    for c in ranked
                    if c.kind == "enc_hadith" and (c.exact or c.score >= 99)
                ),
                None,
            )
            if enc is not None and (
                best is None or best.score < 99 or best.kind == "enc_hadith"
            ):
                best = enc

    second = None
    second_cand: Candidate | None = None
    if best and len(ranked) > 1:
        for c in ranked:
            if (c.kind, c.id, c.norm) != (best.kind, best.id, best.norm):
                second = c.score
                second_cand = c
                break

    # Ambiguous hadith: near-tie between dissimilar matns → abstain
    # (same matn in Bukhari/Muslim is fine — norms are nearly identical)
    status: str
    if (
        best is not None
        and second_cand is not None
        and best.kind in {"hadith", "enc_hadith"}
        and not (best.exact or best.score >= 99.0)
        and (best.score - second_cand.score) < M_MIN
        and float(fuzz.ratio(best.norm, second_cand.norm)) < 80.0
    ):
        status = "UNDETERMINED"
    else:
        status = decide(best, second, n_words)
    if best and best.kind in {"known_claim", "enc_hadith"} and status == "SUPPORTED":
        status = "ATTRIBUTED_RULING"

    matches: list[dict[str, Any]] = []
    for c in ranked[:3]:
        item = _enrich_match(conn, c)
        matches.append(item)

    diff: list[dict[str, Any]] = []
    highlight: list[dict[str, Any]] = []
    user_highlight: list[dict[str, Any]] = []
    correct_text: str | None = None
    matched_span: str | None = None
    gradings: list[dict[str, Any]] = []
    if best:
        correct_text = best.text_display
        if best.kind == "known_claim":
            gradings = _claim_rulings(conn, int(best.id))
        elif best.kind == "enc_hadith" and best.grading:
            gradings = [best.grading]
        elif best.kind == "hadith":
            gradings = _hadith_gradings(conn, int(best.id))
        # Diff paint for Close always; also for Supported when query ≠ full matn
        # (short quote inside a longer source — show green match + amber extras).
        needs_diff_paint = status == "CLOSE_WITH_DIFF" or (
            status == "SUPPORTED"
            and (
                skeleton != best.norm
                or len(skeleton) / max(len(best.norm), 1) < 0.95
            )
        )
        if needs_diff_paint:
            diff = char_diff(skeleton, best.norm)
            highlight = diff_highlight(best.text_display, skeleton, best.norm)
            user_highlight = user_diff_highlight(text, skeleton, best.norm)
            if len(skeleton) / max(len(best.norm), 1) < SHORT_QUERY_LEN_RATIO or (
                skeleton not in best.norm and best.norm not in skeleton
            ):
                matched_span = _matched_display_span(skeleton, best.norm, best.text_display)
            # Keep full source on Supported so Diff Analysis can show amber "extras";
            # Close still prefers the aligned span as the primary correct_text.
            if (
                status == "CLOSE_WITH_DIFF"
                and matched_span
                and len(matched_span) < len(best.text_display) * 0.9
            ):
                correct_text = matched_span
        elif status == "SUPPORTED":
            # Exact full-string match — entire source is green.
            highlight = [{"op": "equal", "text": best.text_display}]
            user_highlight = [{"op": "equal", "text": text}]

    return {
        "status": status,
        "norm_skeleton": skeleton,
        "n_words": n_words,
        "score": round(best.score, 2) if best else None,
        "matches": matches,
        "diff": diff,
        "diff_highlight": highlight,
        "user_diff_highlight": user_highlight,
        "correct_text": correct_text if status in {"CLOSE_WITH_DIFF", "SUPPORTED", "ATTRIBUTED_RULING"} else None,
        "matched_span": matched_span if status in {"CLOSE_WITH_DIFF", "SUPPORTED"} else None,
        "gradings": gradings if status == "ATTRIBUTED_RULING" else [],
        "claim_type": claim_type,
    }


def _enrich_match(conn: sqlite3.Connection, c: Candidate) -> dict[str, Any]:
    item: dict[str, Any] = {
        "kind": c.kind,
        "id": c.id,
        "score": round(c.score, 2),
        "text": c.text_display,
        "ref": c.ref,
        "correct_text": c.text_display,
    }
    proof = _proof_url(c.kind, c.ref)
    if proof:
        item["proof_url"] = proof
        item["ref"] = {**c.ref, "proof_url": proof}
    if c.kind == "known_claim":
        rulings = _claim_rulings(conn, int(c.id))
        item["gradings"] = rulings
        if rulings:
            item["grading"] = rulings[0]
            if rulings[0].get("url"):
                item["proof_url"] = rulings[0]["url"]
    elif c.kind == "enc_hadith":
        if c.grading:
            item["gradings"] = [c.grading]
            item["grading"] = c.grading
        if c.ref.get("url"):
            item["proof_url"] = str(c.ref["url"])
        elif c.ref.get("enc_id"):
            item["proof_url"] = f"https://hadeethenc.com/ar/hadeeth/{c.ref['enc_id']}"
    elif c.kind == "hadith":
        hg = _hadith_gradings(conn, int(c.id))
        if hg:
            item["gradings"] = hg
            item["grading"] = hg[0]
            if hg[0].get("url"):
                item["proof_url"] = hg[0]["url"]
        item["translations"] = _translations(conn, "hadith", int(c.id))
    elif c.kind == "quran":
        item["translations"] = _translations(conn, "quran", int(c.id))
    return item


_STATUS_RANK = {
    "ATTRIBUTED_RULING": 0,
    "CLOSE_WITH_DIFF": 1,
    "SUPPORTED": 2,
    "UNDETERMINED": 3,
}


def match(conn: sqlite3.Connection, text: str) -> dict[str, Any]:
    """Match text: segment claims, retrieve per claim, pick primary card status."""
    claims = segment(text)
    if not claims:
        return _match_one(conn, text, "unknown") | {"claims": []}

    per_claim: list[dict[str, Any]] = []
    for span in claims:
        one = _match_one(conn, span.text, span.claim_type)
        per_claim.append(
            {
                "span": {
                    "text": span.text,
                    "start": span.start,
                    "end": span.end,
                    "claim_type": span.claim_type,
                },
                "status": one["status"],
                "score": one["score"],
                "matches": one["matches"],
                "diff": one["diff"],
                "diff_highlight": one.get("diff_highlight") or [],
                "user_diff_highlight": one.get("user_diff_highlight") or [],
                "correct_text": one.get("correct_text"),
                "matched_span": one.get("matched_span"),
                "gradings": one.get("gradings") or [],
                "norm_skeleton": one["norm_skeleton"],
                "n_words": one["n_words"],
            }
        )

    # Primary = longest span's result, broken by status severity
    primary_idx = max(
        range(len(claims)),
        key=lambda i: (len(claims[i].text), -_STATUS_RANK.get(per_claim[i]["status"], 9)),
    )
    primary = per_claim[primary_idx]
    # If any claim is an attributed ruling on a known fabrication, surface it
    for i, c in enumerate(per_claim):
        if c["status"] == "ATTRIBUTED_RULING":
            primary = c
            primary_idx = i
            break

    return {
        "status": primary["status"],
        "norm_skeleton": primary["norm_skeleton"],
        "n_words": primary["n_words"],
        "score": primary["score"],
        "matches": primary["matches"],
        "diff": primary["diff"],
        "diff_highlight": primary.get("diff_highlight") or [],
        "user_diff_highlight": primary.get("user_diff_highlight") or [],
        "correct_text": primary.get("correct_text"),
        "matched_span": primary.get("matched_span"),
        "gradings": primary.get("gradings") or [],
        "claims": per_claim,
        "primary_claim_index": primary_idx,
    }
