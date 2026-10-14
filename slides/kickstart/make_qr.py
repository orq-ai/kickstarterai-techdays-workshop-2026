"""Write the deck's QR codes as styled SVGs: `uvx --with segno python slides/kickstart/make_qr.py`."""

from pathlib import Path

import segno

INK, ORANGE, CARD = "#141319", "#DF5325", "#F7F3EF"
CODES = {
    "qr-register.svg": "https://orq-kickstart.vercel.app",
    "qr-github.svg": "https://github.com/orq-ai/orq-workshop",
}


def svg(url: str) -> str:
    # error level H survives the logo covering the centre
    matrix = [list(row) for row in segno.make(url, error="h", boost_error=False).matrix]
    n = len(matrix)
    finders = [(0, 0), (0, n - 7), (n - 7, 0)]
    logo = range(n // 2 - 3, n // 2 + 4)

    def skip(r: int, c: int) -> bool:
        in_finder = any(fr <= r < fr + 7 and fc <= c < fc + 7 for fr, fc in finders)
        return in_finder or (r in logo and c in logo)

    dots = "".join(
        f'<circle cx="{c + .5}" cy="{r + .5}" r=".42"/>'
        for r in range(n) for c in range(n) if matrix[r][c] and not skip(r, c)
    )
    eyes = "".join(
        f'<rect x="{c + .5}" y="{r + .5}" width="6" height="6" rx="1.8" fill="none" stroke="{ORANGE}"/>'
        f'<rect x="{c + 2}" y="{r + 2}" width="3" height="3" rx=".9" fill="{INK}"/>'
        for r, c in finders
    )
    m = n // 2 - 3
    mark = (
        f'<rect x="{m}" y="{m}" width="7" height="7" rx="1.8" fill="{INK}"/>'
        f'<circle cx="{n / 2}" cy="{n / 2}" r="1.7" fill="none" stroke="{ORANGE}" stroke-width="1"/>'
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-1 -1 {n + 2} {n + 2}">'
        f'<rect x="-1" y="-1" width="{n + 2}" height="{n + 2}" rx="2" fill="{CARD}"/>'
        f'<g fill="{INK}">{dots}</g>{eyes}{mark}</svg>'
    )


if __name__ == "__main__":
    out = Path(__file__).parent / "assets"
    for name, url in CODES.items():
        (out / name).write_text(svg(url), encoding="utf-8")
        print(f"wrote {out / name} -> {url}")
