"""Render the GitHub contribution calendar as a themed SVG (assets/contributions.svg).

Uses the public https://github-contributions-api.jogruber.de API, so no token is needed.
Run locally with `python scripts/contributions.py`; the workflow refreshes it daily.
"""
import datetime as dt
import json
import os
import urllib.request

USER = os.environ.get("GH_USER", "mrdrakosss")
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "contributions.svg")

SURF = "#111317"; SURF2 = "#171a1f"; LINE = "#ffffff14"; LINE2 = "#ffffff29"
TEXT = "#f3f4ee"; MUTED = "#8c909a"; DIM = "#5b5f68"; ACC = "#a3f02e"
LEVELS = ["#1a1d22", "#2b3a14", "#4f7a18", "#7cc424", ACC]
FONT = "'Geist','Inter','Segoe UI',system-ui,-apple-system,Helvetica,Arial,sans-serif"
MONO = "'Geist Mono','JetBrains Mono',ui-monospace,SFMono-Regular,Consolas,monospace"


def fetch():
    url = f"https://github-contributions-api.jogruber.de/v4/{USER}?y=last"
    req = urllib.request.Request(url, headers={"User-Agent": "profile-readme"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def longest_streak(days):
    best = cur = 0
    for d in days:
        cur = cur + 1 if d["count"] > 0 else 0
        best = max(best, cur)
    return best


def render(data):
    days = data["contributions"]
    total = sum(d["count"] for d in days)
    best_day = max(days, key=lambda d: d["count"])
    streak = longest_streak(days)

    W, H = 1200, 360
    cell, gap = 17, 4
    first = dt.date.fromisoformat(days[0]["date"])
    offset = (first.weekday() + 1) % 7  # GitHub weeks start on Sunday
    weeks = (len(days) + offset + 6) // 7
    grid_w = weeks * (cell + gap) - gap
    gx = (W - grid_w) / 2
    gy = 176

    css = (f".f{{font-family:{FONT}}} .m{{font-family:{MONO}}}"
           "@keyframes pop{from{opacity:0;transform:scale(.4)}to{opacity:1;transform:none}}"
           ".c{transform-box:fill-box;transform-origin:center;animation:pop .5s cubic-bezier(.16,1,.3,1) both}"
           "@media (prefers-reduced-motion:reduce){*{animation:none!important}}")

    b = [f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="22" fill="{SURF}" stroke="{LINE2}"/>',
         f'<text x="{gx}" y="58" class="m" font-size="14" letter-spacing="3" fill="{ACC}">● CONTRIBUTIONS · LAST 12 MONTHS</text>']

    stats = [(f"{total}", "contributions"), (f"{streak}d", "longest streak"),
             (f"{best_day['count']}", "best day")]
    sx = gx
    for val, label in stats:
        b.append(f'<text x="{sx}" y="112" class="f" font-size="40" font-weight="700" letter-spacing="-1" fill="{TEXT}">{val}</text>')
        b.append(f'<text x="{sx}" y="138" class="f" font-size="15" fill="{MUTED}">{label}</text>')
        sx += 230

    # month labels
    last_month = None
    for i, d in enumerate(days):
        date = dt.date.fromisoformat(d["date"])
        if date.day <= 7 and date.month != last_month and (i + offset) % 7 == 0:
            x = gx + ((i + offset) // 7) * (cell + gap)
            if x < gx + grid_w - 30:
                b.append(f'<text x="{x}" y="{gy-10}" class="m" font-size="12" fill="{DIM}">{date.strftime("%b")}</text>')
            last_month = date.month

    for i, d in enumerate(days):
        col, row = divmod(i + offset, 7)
        x = gx + col * (cell + gap)
        y = gy + row * (cell + gap)
        delay = col * 0.025
        b.append(f'<rect class="c" style="animation-delay:{delay:.3f}s" x="{x}" y="{y}" width="{cell}" height="{cell}" rx="4" '
                 f'fill="{LEVELS[d["level"]]}" stroke="{LINE}"><title>{d["date"]}: {d["count"]}</title></rect>')

    # legend
    lx = gx + grid_w - (5 * (12 + 4)) - 4
    ly = 104
    b.append(f'<text x="{lx-10}" y="{ly+10}" text-anchor="end" class="m" font-size="12" fill="{DIM}">less</text>')
    for k, c in enumerate(LEVELS):
        b.append(f'<rect x="{lx + k*16}" y="{ly}" width="12" height="12" rx="3" fill="{c}" stroke="{LINE}"/>')
    b.append(f'<text x="{lx + 5*16 + 6}" y="{ly+10}" class="m" font-size="12" fill="{DIM}">more</text>')

    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
            f'aria-label="{total} contributions in the last year"><title>{total} contributions in the last year</title>'
            f'<style>{css}</style>{"".join(b)}</svg>')


if __name__ == "__main__":
    svg = render(fetch())
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print("wrote", os.path.normpath(OUT))
