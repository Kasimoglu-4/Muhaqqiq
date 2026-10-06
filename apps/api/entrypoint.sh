#!/bin/sh
set -eu
DB_PATH="${MUHAQQIQ_DB:-/data/muhaqqiq.db}"
DB_DIR=$(dirname "$DB_PATH")
mkdir -p "$DB_DIR"
# Seed from baked corpus on first boot (cards persist only if DB_PATH is on a volume).
if [ ! -f "$DB_PATH" ]; then
  echo "Seeding $DB_PATH from image corpus"
  cp /app/data/build/muhaqqiq.db "$DB_PATH"
fi
exec uvicorn muhaqqiq.main:app --host 0.0.0.0 --port "${PORT:-8000}"
