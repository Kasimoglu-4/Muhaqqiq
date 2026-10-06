#!/bin/sh
set -eu
# Seed persistent volume with baked corpus on first boot (cards live on the volume).
if [ ! -f /data/muhaqqiq.db ]; then
  echo "Seeding /data/muhaqqiq.db from image corpus"
  cp /app/data/build/muhaqqiq.db /data/muhaqqiq.db
fi
exec uvicorn muhaqqiq.main:app --host 0.0.0.0 --port "${PORT:-8000}"
