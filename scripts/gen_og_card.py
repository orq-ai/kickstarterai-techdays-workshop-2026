"""Render docs/assets/og-image.html to the committed Open Graph PNG.

Run with: uv run --with playwright python scripts/gen_og_card.py
"""

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "assets" / "og-image.html"
OUTPUT = ROOT / "docs" / "assets" / "og-image.png"

with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    page = browser.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=1)
    page.goto(SOURCE.resolve().as_uri())
    page.evaluate("document.fonts.ready")
    page.screenshot(path=str(OUTPUT))
    browser.close()

print(OUTPUT.relative_to(ROOT))
