"""SQLite connection and schema (default runtime). Postgres schema in schema/postgres.sql."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from muhaqqiq import DATA_VERSION

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB = ROOT / "data" / "build" / "muhaqqiq.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  url TEXT,
  license TEXT,
  attribution TEXT,
  version TEXT,
  retrieved_at TEXT
);

CREATE TABLE IF NOT EXISTS quran_verses (
  id INTEGER PRIMARY KEY,
  sura INTEGER NOT NULL,
  aya INTEGER NOT NULL,
  text_uthmani TEXT NOT NULL,
  text_clean TEXT NOT NULL,
  norm_skeleton TEXT NOT NULL,
  source_id INTEGER REFERENCES sources(id),
  UNIQUE (sura, aya)
);

CREATE TABLE IF NOT EXISTS hadiths (
  id INTEGER PRIMARY KEY,
  collection TEXT NOT NULL,
  number TEXT NOT NULL,
  text_ar TEXT NOT NULL,
  text_clean TEXT NOT NULL,
  norm_skeleton TEXT NOT NULL,
  enc_id TEXT,
  proof_url TEXT,
  source_id INTEGER REFERENCES sources(id),
  UNIQUE (collection, number)
);

CREATE TABLE IF NOT EXISTS known_claims (
  id INTEGER PRIMARY KEY,
  text_ar TEXT NOT NULL,
  norm_skeleton TEXT NOT NULL,
  claim_type TEXT NOT NULL,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS known_claim_rulings (
  id INTEGER PRIMARY KEY,
  claim_id INTEGER NOT NULL REFERENCES known_claims(id),
  grader TEXT NOT NULL,
  ruling TEXT NOT NULL,
  reference TEXT NOT NULL,
  url TEXT,
  source_id INTEGER REFERENCES sources(id)
);

CREATE TABLE IF NOT EXISTS gradings (
  id INTEGER PRIMARY KEY,
  hadith_id INTEGER REFERENCES hadiths(id),
  grader TEXT NOT NULL,
  grade_label TEXT NOT NULL,
  grade_normalized TEXT,
  reference TEXT NOT NULL,
  url TEXT,
  source_id INTEGER REFERENCES sources(id)
);

CREATE TABLE IF NOT EXISTS translations (
  id INTEGER PRIMARY KEY,
  kind TEXT NOT NULL,
  ref_id INTEGER NOT NULL,
  lang TEXT NOT NULL,
  text TEXT NOT NULL,
  source_id INTEGER REFERENCES sources(id)
);

CREATE TABLE IF NOT EXISTS enc_hadiths (
  id INTEGER PRIMARY KEY,
  enc_id TEXT NOT NULL UNIQUE,
  text_ar TEXT NOT NULL,
  norm_skeleton TEXT NOT NULL,
  attribution TEXT,
  grade TEXT,
  reference TEXT,
  url TEXT,
  source_id INTEGER REFERENCES sources(id)
);

CREATE TABLE IF NOT EXISTS cards (
  id TEXT PRIMARY KEY,
  input_hash TEXT NOT NULL,
  status TEXT NOT NULL,
  match_refs TEXT NOT NULL,
  score REAL,
  diff_json TEXT NOT NULL DEFAULT '[]',
  extras_json TEXT NOT NULL DEFAULT '{}',
  data_version TEXT NOT NULL,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE VIRTUAL TABLE IF NOT EXISTS quran_fts USING fts5(
  norm_skeleton, verse_id UNINDEXED, content='', tokenize='unicode61'
);

CREATE VIRTUAL TABLE IF NOT EXISTS hadith_fts USING fts5(
  norm_skeleton, hadith_id UNINDEXED, content='', tokenize='unicode61'
);

CREATE VIRTUAL TABLE IF NOT EXISTS claims_fts USING fts5(
  norm_skeleton, claim_id UNINDEXED, content='', tokenize='unicode61'
);

CREATE INDEX IF NOT EXISTS idx_quran_norm ON quran_verses(norm_skeleton);
CREATE INDEX IF NOT EXISTS idx_hadith_norm ON hadiths(norm_skeleton);
CREATE INDEX IF NOT EXISTS idx_claims_norm ON known_claims(norm_skeleton);

CREATE TABLE IF NOT EXISTS feedback (
  id TEXT PRIMARY KEY,
  card_id TEXT,
  kind TEXT NOT NULL,
  comment TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);
"""


def db_path() -> Path:
    return Path(os.environ.get("MUHAQQIQ_DB", DEFAULT_DB))


def connect(path: Path | None = None) -> sqlite3.Connection:
    p = path or db_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(p)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    cols = {row[1] for row in conn.execute("PRAGMA table_info(cards)").fetchall()}
    if cols and "diff_json" not in cols:
        conn.execute("ALTER TABLE cards ADD COLUMN diff_json TEXT NOT NULL DEFAULT '[]'")
    if cols and "extras_json" not in cols:
        conn.execute("ALTER TABLE cards ADD COLUMN extras_json TEXT NOT NULL DEFAULT '{}'")
    hcols = {row[1] for row in conn.execute("PRAGMA table_info(hadiths)").fetchall()}
    if hcols and "enc_id" not in hcols:
        conn.execute("ALTER TABLE hadiths ADD COLUMN enc_id TEXT")
    if hcols and "proof_url" not in hcols:
        conn.execute("ALTER TABLE hadiths ADD COLUMN proof_url TEXT")


def init_db(conn: sqlite3.Connection | None = None) -> sqlite3.Connection:
    own = conn is None
    conn = conn or connect()
    conn.executescript(SCHEMA)
    _migrate(conn)
    conn.commit()
    if own:
        return conn
    return conn


def data_version() -> str:
    return DATA_VERSION
