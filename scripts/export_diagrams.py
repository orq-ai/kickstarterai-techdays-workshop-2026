"""Export inline-SVG diagram sources to committed 2x PNGs.

Run `make diagrams`. Install Chromium once when prompted:
`uv run --with playwright playwright install chromium`.
"""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
files = [Path(arg) for arg in sys.argv[1:]] or sorted(ROOT.glob("modules/*/assets/*.html"))

with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    page = browser.new_page(device_scale_factor=2)
    for source in files:
        page.goto(source.resolve().as_uri())
        page.wait_for_load_state("networkidle")
        page.evaluate("document.fonts.ready")
        output = source.with_suffix(".png")
        page.locator("svg").first.screenshot(path=str(output), omit_background=True)
        print(f"{output.relative_to(ROOT)}")
    browser.close()
