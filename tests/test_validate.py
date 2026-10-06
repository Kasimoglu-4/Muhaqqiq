"""Data validation tests (requires built DB)."""

from pathlib import Path

import pytest

from muhaqqiq.db import DEFAULT_DB, connect, init_db
from pipeline.sura_lengths import SURA_VERSE_COUNTS
from pipeline.validate import validate_sqlite

pytestmark = pytest.mark.skipif(not DEFAULT_DB.exists(), reason="DB not built; run make data")


def test_sura_lengths_sum():
    assert len(SURA_VERSE_COUNTS) == 114
    assert sum(SURA_VERSE_COUNTS) == 6236


def test_validate_sqlite_passes():
    conn = init_db(connect())
    try:
        validate_sqlite(conn)
    finally:
        conn.close()


def test_sources_in_readme():
    text = Path("README.md").read_text(encoding="utf-8")
    assert "Tanzil" in text
    assert "Dorar" in text
