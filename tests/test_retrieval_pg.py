"""Postgres trigram shortlist — skipped unless DATABASE_URL points at loaded DB."""


import pytest

from muhaqqiq.normalize import normalize
from muhaqqiq.retrieval_pg import pg_url, trigram_shortlist

pytestmark = pytest.mark.skipif(not pg_url(), reason="DATABASE_URL not set")


def test_trigram_finds_niyat():
    rows = trigram_shortlist(normalize("إنما الأعمال بالنيات"), kind="hadith", limit=20)
    assert rows, "expected trigram hits for famous matn"
    assert any(
        "بالنيات" in (r["norm_skeleton"] or "") or "بالنيه" in (r["norm_skeleton"] or "")
        for r in rows
    )


def test_trigram_finds_ikhlas():
    rows = trigram_shortlist(normalize("قل هو الله احد"), kind="quran", limit=20)
    assert rows
    assert any(r.get("sura") == 112 for r in rows)
