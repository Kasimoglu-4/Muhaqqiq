FROM python:3.12-slim AS build

WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY pipeline ./pipeline
COPY data/fabricated_seed.csv ./data/fabricated_seed.csv

RUN uv sync --frozen --no-dev \
  && uv run python -m pipeline.download_sources \
  && uv run python -m pipeline.load_all \
  && uv run python -m pipeline.validate

FROM python:3.12-slim

WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY pipeline ./pipeline
COPY data/fabricated_seed.csv ./data/fabricated_seed.csv
COPY --from=build /app/data/build/muhaqqiq.db ./data/build/muhaqqiq.db
COPY apps/api/entrypoint.sh /entrypoint.sh

RUN uv sync --frozen --no-dev \
  && chmod +x /entrypoint.sh \
  && mkdir -p /data

ENV PATH="/app/.venv/bin:$PATH"
ENV MUHAQQIQ_DB=/data/muhaqqiq.db
ENV MUHAQQIQ_OCR=stub
EXPOSE 8000
CMD ["/entrypoint.sh"]
