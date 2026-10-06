-- Muhaqqiq Phase 1 Postgres schema
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS sources (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  url TEXT,
  license TEXT,
  attribution TEXT,
  version TEXT,
  retrieved_at DATE
);

CREATE TABLE IF NOT EXISTS quran_verses (
  id SERIAL PRIMARY KEY,
  sura INT NOT NULL,
  aya INT NOT NULL,
  text_uthmani TEXT NOT NULL,
  text_clean TEXT NOT NULL,
  norm_skeleton TEXT NOT NULL,
  source_id INT REFERENCES sources(id),
  UNIQUE (sura, aya)
);

CREATE TABLE IF NOT EXISTS hadiths (
  id SERIAL PRIMARY KEY,
  collection TEXT NOT NULL,
  number TEXT NOT NULL,
  text_ar TEXT NOT NULL,
  text_clean TEXT NOT NULL,
  norm_skeleton TEXT NOT NULL,
  enc_id TEXT,
  proof_url TEXT,
  embedding vector(1024),
  source_id INT REFERENCES sources(id),
  UNIQUE (collection, number)
);

CREATE TABLE IF NOT EXISTS gradings (
  id SERIAL PRIMARY KEY,
  hadith_id INT REFERENCES hadiths(id),
  grader TEXT NOT NULL,
  grade_label TEXT NOT NULL,
  grade_normalized TEXT,
  reference TEXT NOT NULL,
  url TEXT,
  source_id INT REFERENCES sources(id)
);

CREATE TABLE IF NOT EXISTS known_claims (
  id SERIAL PRIMARY KEY,
  text_ar TEXT NOT NULL,
  norm_skeleton TEXT NOT NULL,
  embedding vector(1024),
  claim_type TEXT NOT NULL,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS known_claim_rulings (
  id SERIAL PRIMARY KEY,
  claim_id INT NOT NULL REFERENCES known_claims(id),
  grader TEXT NOT NULL,
  ruling TEXT NOT NULL,
  reference TEXT NOT NULL,
  url TEXT,
  source_id INT REFERENCES sources(id)
);

CREATE TABLE IF NOT EXISTS translations (
  id SERIAL PRIMARY KEY,
  kind TEXT NOT NULL,
  ref_id INT NOT NULL,
  lang TEXT NOT NULL,
  text TEXT NOT NULL,
  source_id INT REFERENCES sources(id)
);

CREATE TABLE IF NOT EXISTS enc_hadiths (
  id SERIAL PRIMARY KEY,
  enc_id TEXT NOT NULL UNIQUE,
  text_ar TEXT NOT NULL,
  norm_skeleton TEXT NOT NULL,
  attribution TEXT,
  grade TEXT,
  reference TEXT,
  url TEXT,
  source_id INT REFERENCES sources(id)
);

CREATE TABLE IF NOT EXISTS cards (
  id TEXT PRIMARY KEY,
  input_hash TEXT NOT NULL,
  status TEXT NOT NULL,
  match_refs JSONB NOT NULL,
  score REAL,
  data_version TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_quran_norm_trgm ON quran_verses USING gin (norm_skeleton gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_hadith_norm_trgm ON hadiths USING gin (norm_skeleton gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_claims_norm_trgm ON known_claims USING gin (norm_skeleton gin_trgm_ops);
