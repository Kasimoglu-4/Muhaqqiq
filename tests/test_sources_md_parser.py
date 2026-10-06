from pathlib import Path

from pipeline.parse_sources_md import parse_sources_md

ROOT = Path(__file__).resolve().parents[1]


def test_parse_sources_includes_tanzil_and_dorar():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    rows = parse_sources_md(text)
    names = " ".join(r["name"] for r in rows)
    assert "Tanzil" in names
    assert "Dorar" in names
    assert len(rows) >= 5


def test_parse_sources_marks_used_vs_blocked():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    rows = parse_sources_md(text)
    by_name = {r["name"]: r for r in rows}
    assert by_name["Tanzil.net (via quran-json)"]["status"] == "used"
    assert by_name["QuranEnc API"]["status"] == "used"
    assert by_name["Dorar al-Sunniyyah"]["status"] == "blocked"
    assert by_name["King Fahd Complex / Quranpedia"]["status"] == "link_out"
    assert all('"' not in r["attribution"] for r in rows)


def test_parse_sources_includes_urls():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    rows = parse_sources_md(text)
    by_name = {r["name"]: r for r in rows}
    assert by_name["Tanzil.net (via quran-json)"]["url"] == "https://tanzil.net/"
    assert by_name["fawazahmed0/hadith-api"]["url"].startswith("https://github.com/")
    assert by_name["QuranEnc API"]["url"] == "https://quranenc.com/"
    assert by_name["HadeethEnc API"]["url"] == "https://hadeethenc.com/"
    assert by_name["Curated fabricated/weak seed"]["url"] == ""
