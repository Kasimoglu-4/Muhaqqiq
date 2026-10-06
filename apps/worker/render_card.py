"""Playwright card PNG renderer (Phase 4.3).

Usage (after API is up and Playwright is installed):

    uv sync --group worker
    uv run playwright install chromium
    uv run python -m apps.worker.render_card --card-id <id> --out card.png
"""

from __future__ import annotations

import argparse
from pathlib import Path


def render(card_url: str, out: Path, *, width: int = 1080, height: int = 1350) -> Path:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise SystemExit("Install worker deps: uv sync --group worker && playwright install chromium") from e

    out.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=2)
        page.goto(card_url, wait_until="networkidle")
        page.screenshot(path=str(out), full_page=False)
        browser.close()
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--card-id", required=True)
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    parser.add_argument("--out", default="data/build/card.png")
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1350)
    args = parser.parse_args()
    path = render(
        f"{args.base.rstrip('/')}/c/{args.card_id}",
        Path(args.out),
        width=args.width,
        height=args.height,
    )
    print(path)


if __name__ == "__main__":
    main()
