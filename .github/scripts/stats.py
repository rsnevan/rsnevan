"""Render assets/stats.svg from the GitHub GraphQL API, styled to match rsnevan.vercel.app."""
import json
import os
import urllib.request
from collections import Counter
from html import escape

USER = os.environ.get("GH_USER", "rsnevan")
TOKEN = os.environ["GITHUB_TOKEN"]
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "stats.svg")

QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    contributionsCollection { contributionCalendar { totalContributions } }
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { nodes { name } }
      }
    }
  }
}
"""

# languages that say little about what someone builds
SKIP = {"HTML", "CSS", "SCSS", "Shell", "Batchfile", "PowerShell", "Dockerfile", "Makefile", "Procfile"}

BG, SURFACE, BORDER = "#0a0a0b", "#111113", "#222226"
TEXT, MUTED, DIM = "#f0efe8", "#7a7a82", "#62626b"
BAR_COLORS = ["#c8f04a", "#4af0c8", "#f04a8c", "#7a7a82", "#62626b"]
MONO = "ui-monospace,SFMono-Regular,'DM Mono',Consolas,Menlo,monospace"
SANS = "'DM Sans','Segoe UI',-apple-system,Helvetica,Arial,sans-serif"


def fetch():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(data["errors"])
    return data["data"]["user"]


def render(u):
    repos = u["repositories"]["nodes"]
    stats = [
        (u["contributionsCollection"]["contributionCalendar"]["totalContributions"], "CONTRIBUTIONS"),
        (sum(r["stargazerCount"] for r in repos), "STARS"),
        (u["repositories"]["totalCount"], "REPOS"),
        (u["followers"]["totalCount"], "FOLLOWERS"),
    ]
    langs = Counter(l["name"] for r in repos for l in r["languages"]["nodes"] if l["name"] not in SKIP)
    top = langs.most_common(5)
    peak = max((n for _, n in top), default=1)

    W, H = 900, 210
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        "<style>",
        f".n{{font:400 34px {SANS};fill:{TEXT}}}",
        f".l{{font:500 10px {MONO};fill:{DIM};letter-spacing:1.6px}}",
        f".h{{font:500 10px {MONO};fill:{MUTED};letter-spacing:2px}}",
        f".k{{font:400 12px {MONO};fill:{MUTED}}}",
        ".bar{transform-box:fill-box;transform-origin:left;animation:grow 1.1s cubic-bezier(.2,.8,.2,1) both}",
        "@keyframes grow{from{transform:scaleX(0)}}",
        ".fade{animation:fade .8s ease both}@keyframes fade{from{opacity:0}}",
        "</style>",
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="10" fill="{SURFACE}" stroke="{BORDER}"/>',
        f'<text x="32" y="40" class="h">GITHUB STATS</text>',
    ]
    for i, (n, label) in enumerate(stats):
        x = (32, 168, 268, 360)[i]
        d = f"{i*0.12:.2f}s"
        out.append(f'<g class="fade" style="animation-delay:{d}">'
                   f'<text x="{x}" y="118" class="n">{n}</text>'
                   f'<text x="{x}" y="142" class="l">{label}</text></g>')
    out.append(f'<line x1="452" y1="32" x2="452" y2="{H-32}" stroke="{BORDER}"/>')
    out.append(f'<text x="484" y="40" class="h">TOP LANGUAGES</text>')
    for i, (name, n) in enumerate(top):
        y = 70 + i * 26
        w = 260 * n / peak
        c = BAR_COLORS[i % len(BAR_COLORS)]
        out.append(f'<text x="484" y="{y+4}" class="k">{escape(name)}</text>')
        out.append(f'<rect x="590" y="{y}" width="260" height="2" fill="{BORDER}"/>')
        out.append(f'<rect class="bar" style="animation-delay:{0.3+i*0.1:.2f}s" x="590" y="{y}" width="{w:.1f}" height="2" fill="{c}"/>')
        out.append(f'<text x="868" y="{y+4}" class="k" text-anchor="end">{n}</text>')
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(render(fetch()))
    print("wrote", os.path.normpath(OUT))
