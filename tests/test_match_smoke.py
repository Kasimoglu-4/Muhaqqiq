"""Phase 0 done-criteria smoke tests (requires built DB)."""


import pytest

from muhaqqiq.db import DEFAULT_DB, connect, init_db
from muhaqqiq.match import match

pytestmark = pytest.mark.skipif(not DEFAULT_DB.exists(), reason="DB not built; run make data")


@pytest.fixture(scope="module")
def conn():
    init_db()
    c = connect()
    yield c
    c.close()


def test_niyat_supported_bukhari(conn):
    r = match(conn, "إنما الأعمال بالنيات")
    assert r["status"] == "SUPPORTED"
    assert r["matches"][0]["ref"]["collection"] == "Bukhari"


def test_tampered_verse_close(conn):
    r = match(conn, "بسم الله الرحمن الكريم")
    assert r["status"] == "CLOSE_WITH_DIFF"
    assert r["diff"]


def test_made_up_undetermined(conn):
    r = match(conn, "قال رسول الله من أكل تفاحة حمراء غفر له")
    assert r["status"] == "UNDETERMINED"


def test_fabricated_attributed(conn):
    r = match(conn, "اطلبوا العلم ولو في الصين")
    assert r["status"] == "ATTRIBUTED_RULING"


def test_short_vocab_overlap_undetermined(conn):
    """Scattered rain/sky tokens must not Close against a long istisqāʾ hadith."""
    r = match(conn, "ان تمطر السماء")
    assert r["status"] == "UNDETERMINED"
    assert r["n_words"] < 4


def test_single_token_khayrukum_undetermined(conn):
    """«خيركم» alone is a common stem inside many hadiths — abstain."""
    r = match(conn, "خيركم")
    assert r["status"] == "UNDETERMINED"
    assert r["n_words"] == 1
