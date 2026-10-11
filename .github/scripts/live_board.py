#!/usr/bin/env python3
"""Rebuild assets/live.svg, the "Shipping log" on the profile, from the GitHub API.

Run by .github/workflows/live-board.yml. Standard library only. The output depends only
on repository data (no "today" in it), so the workflow commits only when something
actually shipped.

    GITHUB_TOKEN=... python .github/scripts/live_board.py
"""
import json
import os
import urllib.request
from html import escape

USER = "akeanti"
EXCLUDE = {"akeanti", "1969", "akeanti.github.io"}  # profile repo and jokes stay off the board
ROWS = 5
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "live.svg")

QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      totalCount
      nodes {
        name description pushedAt stargazerCount isArchived
        primaryLanguage { name color }
        latestRelease { tagName }
      }
    }
  }
}
"""

BG, PANEL, LINE = "#181e1c", "#1d2522", "#3b4a42"
TEXT, MUTED, SAGE, TEAL, AMBER = "#f4f0e5", "#b8c5b9", "#b7cd91", "#48bfc4", "#e0a84a"


def fetch():
    token = os.environ["GITHUB_TOKEN"]
    body = json.dumps({"query": QUERY, "variables": {"login": USER}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "Authorization": f"Bearer {token}", "Content-Type": "application/json", "User-Agent": f"{USER}-profile"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    if "errors" in data:
        raise SystemExit(f"GraphQL errors: {data['errors']}")
    return data["data"]["user"]


def e(s):
    return escape(s, quote=True)


def clip(s, n):
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[: n - 1].rstrip(" ,.;:·-") + "…"


def render(user):
    repos = user["repositories"]["nodes"]
    stars = sum(r["stargazerCount"] for r in repos)
    shown = [r for r in repos if r["name"] not in EXCLUDE and not r["isArchived"] and r["description"]][:ROWS]

    W, top, rh = 1200, 128, 64
    H = top + rh * len(shown) + 70
    o = []
    o.append(f'<text x="34" y="60" font-size="36" class="serif">Shipping log.</text>')
    o.append(f'<circle cx="904" cy="49" r="4" fill="{TEAL}" class="pulse"/>'
             f'<text x="1166" y="54" font-size="14" class="mono" text-anchor="end" style="fill:{SAGE}">AUTO-UPDATED FROM GITHUB</text>')
    o.append(f'<text x="34" y="92" font-size="12.5" class="mono" style="fill:{MUTED}">LATEST PUBLIC PUSHES · REBUILT BY GITHUB ACTIONS</text>')
    o.append(f'<path d="M34 {top - 18}H1166" stroke="{LINE}"/>')
    for i, r in enumerate(shown):
        y = top + i * rh
        lang = r["primaryLanguage"] or {}
        color = lang.get("color") or MUTED
        g = [f'<g class="row" style="animation-delay:{0.15 + i * 0.12:.2f}s">']
        g.append(f'<circle cx="42" cy="{y + 9}" r="6" fill="{e(color)}"/>')
        if i == 0:
            g.append(f'<circle cx="42" cy="{y + 9}" r="6" stroke="{e(color)}" class="ring"/>')
        g.append(f'<text x="62" y="{y + 16}" font-size="20" class="bold">{e(r["name"])}</text>')
        g.append(f'<text x="62" y="{y + 40}" font-size="15" style="fill:{MUTED}">{e(clip(r["description"], 96))}</text>')
        x = 1166
        date = r["pushedAt"][:10]
        g.append(f'<text x="{x}" y="{y + 15}" font-size="13" class="tl" text-anchor="end" style="fill:{MUTED}">{date}</text>')
        x -= 104
        g.append(f'<text x="{x}" y="{y + 15}" font-size="14" class="tl" text-anchor="end" style="fill:{AMBER}">★ {r["stargazerCount"]}</text>')
        x -= 58
        rel = r["latestRelease"]
        if rel:
            tag = clip(rel["tagName"], 14)
            w = round(len(tag) * 7.8 + 22, 1)
            g.append(f'<rect x="{x - w}" y="{y - 2}" width="{w}" height="22" rx="11" stroke="{SAGE}" stroke-opacity=".8"/>'
                     f'<text x="{x - w / 2:.1f}" y="{y + 13}" font-size="12" class="tl" text-anchor="middle" style="fill:{SAGE}">{e(tag)}</text>')
            x -= w + 12
        if i == 0:
            g.append(f'<text x="{x}" y="{y + 15}" font-size="11.5" class="mono" text-anchor="end" style="fill:{TEAL}">LATEST</text>')
        if lang.get("name"):
            g.append(f'<text x="1166" y="{y + 40}" font-size="12.5" class="tl" text-anchor="end" style="fill:{MUTED}">{e(lang["name"])}</text>')
        g.append(f'<path d="M34 {y + rh - 12}H1166" stroke="{LINE}" stroke-opacity=".6"/>')
        g.append("</g>")
        o.append("".join(g))
    fy = H - 30
    total = user["repositories"]["totalCount"]
    o.append(f'<text x="34" y="{fy}" font-size="13" class="mono" style="fill:{MUTED}">{total} PUBLIC REPOS · ★ {stars} STARS · '
             f'{user["followers"]["totalCount"]} FOLLOWERS</text>')
    o.append(f'<text x="1166" y="{fy}" font-size="13" class="mono" text-anchor="end" style="fill:{SAGE}">GITHUB.COM/{USER.upper()}</text>')

    desc = "Shipping log, rebuilt from the GitHub API. Latest public pushes: " + "; ".join(
        f'{r["name"]}: {clip(r["description"], 96).rstrip(".")}' + (f' (release {r["latestRelease"]["tagName"]})' if r["latestRelease"] else "")
        for r in shown) + f". {total} public repositories, {stars} stars."
    css = """text{font-family:Segoe UI,Arial,sans-serif;fill:#f4f0e5}
.serif{font-family:Georgia,Times New Roman,serif;letter-spacing:-1.7px}
.mono{font-family:Consolas,Liberation Mono,Menlo,monospace;letter-spacing:1.4px}
.tl{font-family:Consolas,Liberation Mono,Menlo,monospace;letter-spacing:0}
.bold{font-weight:650;letter-spacing:-.4px}
.pulse{animation:pulse 2.4s ease-in-out infinite}@keyframes pulse{0%,100%{opacity:.35}50%{opacity:1}}
.ring{animation:ring 2.4s ease-out infinite;transform-box:fill-box;transform-origin:center}@keyframes ring{0%{transform:scale(1);opacity:.7}100%{transform:scale(2.6);opacity:0}}
.row{animation:row .7s cubic-bezier(.2,.7,.2,1) both}@keyframes row{from{opacity:0;transform:translateY(10px)}}
@media(prefers-reduced-motion:reduce){*{animation:none!important}}"""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none" role="img" '
            f'aria-labelledby="title desc"><title id="title">Shipping log</title><desc id="desc">{e(desc)}</desc>'
            f'<defs><style>\n{css}\n</style><clipPath id="bounds"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="24" fill="white"/></clipPath></defs>'
            f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="24" fill="{BG}" stroke="{LINE}"/><g clip-path="url(#bounds)">\n'
            + "\n".join(o) + "\n</g></svg>\n")


if __name__ == "__main__":
    svg = render(fetch())
    path = os.path.normpath(OUT)
    old = open(path, encoding="utf8").read() if os.path.exists(path) else None
    if svg != old:
        with open(path, "w", encoding="utf8", newline="\n") as fh:
            fh.write(svg)
        print(f"updated {path}")
    else:
        print("no change")
