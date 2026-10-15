#!/usr/bin/env python3
"""Build every SVG on the profile, and the pinned-projects block of README.md, from the GitHub API.

Run by .github/workflows/profile.yml every six hours. Standard library only.

    GITHUB_TOKEN=... python .github/scripts/build_profile.py            # fetch, then build
    python .github/scripts/build_profile.py --data snapshot.json        # build from a saved response
    GITHUB_TOKEN=... python .github/scripts/build_profile.py --save snapshot.json

Live:   header.svg (now building, latest release), pin-N.svg (one card per GitHub pin, in pin
        order, with release, CI state, stars and last push), stats.svg (activity, languages).
Static: kpis.svg, skills.svg, section-*.svg, btn-*.svg, contact.svg. Same theme, same script.

Outputs depend only on GitHub data, never on the wall clock, so the workflow commits only when
something changed: a push, a release, a star, a new pin, or another day of contributions.
"""
import argparse
import base64
import datetime as dt
import json
import os
import re
import urllib.request
from html import escape
from xml.etree import ElementTree

USER = "akeanti"
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ASSETS = os.path.join(ROOT, "assets")
README = os.path.join(ROOT, "README.md")
SKIP = {"akeanti", "1969"}  # the profile repo and the Unix-epoch joke stay out of "now building"

BG, PANEL, CHIP, LINE = "#181e1c", "#1f2724", "#232d29", "#33413b"
TEXT, MUTED, DIM = "#f4f0e5", "#a9b8ad", "#728278"
SAGE, TEAL, AMBER, CORAL, INK = "#b7cd91", "#48bfc4", "#e0a84a", "#e5735c", "#16201b"
HEAT = ["#232d29", "#3b5640", "#5a8450", "#86ad68", "#b7cd91"]

QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    contributionsCollection { contributionCalendar { weeks { contributionDays { date contributionCount } } } }
    pinnedItems(first: 6, types: REPOSITORY) { nodes { ... on Repository {
      name description url stargazerCount pushedAt
      primaryLanguage { name color }
      latestRelease { tagName publishedAt }
      defaultBranchRef { target { ... on Commit { statusCheckRollup { state } } } }
    } } }
    repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      totalCount
      nodes {
        name description pushedAt stargazerCount isArchived
        latestRelease { tagName publishedAt }
        languages(first: 8, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } }
      }
    }
  }
}
"""

# How each pinned repo is presented. A repo pinned later without an entry here still gets a card,
# built from its description and language.
PROJECTS = {
    "cascade-gnn": dict(
        tag="MACHINE LEARNING · GRIDS", stage="v0.3", art="cascade", glyph="graph",
        pitch="Early warning for cascading grid failures: five graph neural networks against XGBoost "
              "on PowerGraph (NeurIPS 2024), with edge attributions you can check.",
        metrics=[("5 GNNs", "vs tuned XGBoost baselines"), ("3 splits", "leakage-checked evaluation")],
        stack="PyTorch · XGBoost · Streamlit · Docker"),
    "swingbus": dict(
        tag="POWER SYSTEMS", stage="v0.1", art="oneline", glyph="bus",
        pitch="Power flow, N-1 contingency screening and DC optimal power flow with LMPs for "
              "transmission grids, in about 3,000 lines of NumPy and SciPy.",
        metrics=[("10^{−13} pu", "agreement with PYPOWER"), ("8.3 ms", "full N-1 screen, 118 buses")],
        stack="Python · NumPy · SciPy · mypy strict"),
    "nabd": dict(
        tag="GRID SENSING · IoT", stage="PRE-RELEASE", art="wave", glyph="wave",
        pitch="Open network of GPS-synchronized ESP32-S3 nodes measuring grid frequency, ROCOF and "
              "synchrophasors (IEEE C37.118), with a live map and open data.",
        metrics=[("$59", "per node, bill of materials"), ("C37.118", "IEEE synchrophasor format")],
        stack="C · ESP-IDF · Python · TypeScript · KiCad"),
    "matlab-discord-rpc": dict(
        title="drpc", tag="DEVELOPER TOOLS", art="presence", glyph="presence",
        pitch="Discord Rich Presence for MATLAB and Simulink: shows what you are editing, running, "
              "debugging or simulating. Runs inside MATLAB, no Python or Node.",
        metrics=[("9", "activity states detected"), ("1 line", "install from MATLAB")],
        stack="MATLAB · C# · .NET · Windows"),
    "ariadne": dict(
        tag="ROBOTICS · CONTROL", art="maze", glyph="maze",
        pitch="Simulation-first ESP32 micromouse: clothoid turn synthesis, time-optimal planning and "
              "a 10 kHz physics model running the real firmware control law.",
        metrics=[("2.4×", "faster than stop-and-pivot"), ("115", "automated tests in CI")],
        stack="C++ · Python · FreeRTOS · ESP32"),
    "malfoid": dict(
        tag="EMBEDDED · IoT", stage="ACTIVE BUILD", art="spell", glyph="wand",
        pitch="ESP32-S3 gesture wand: on-device spell recognition from a 6-axis IMU, haptics, and "
              "smart-home control through Home Assistant and MQTT.",
        metrics=[("99.6%", "top-1 accuracy on test casts"), ("~1 ms", "inference on the ESP32-S3")],
        stack="C++ · ESP32-S3 · MQTT · Web Serial"),
}

CSS = f"""text{{font-family:'Segoe UI',-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif;fill:{TEXT}}}
.serif{{font-family:Georgia,'Times New Roman',serif}}.mono{{font-family:Consolas,'SF Mono',Menlo,'Liberation Mono',monospace}}
.b{{font-weight:650}}.mu{{fill:{MUTED}}}.dim{{fill:{DIM}}}.sage{{fill:{SAGE}}}.teal{{fill:{TEAL}}}.amber{{fill:{AMBER}}}.ink{{fill:{INK}}}
.pulse{{animation:pulse 2.4s ease-in-out infinite}}@keyframes pulse{{0%,100%{{opacity:.35}}50%{{opacity:1}}}}
.ring{{animation:ring 2.4s ease-out infinite;transform-box:fill-box;transform-origin:center}}@keyframes ring{{0%{{transform:scale(1);opacity:.8}}100%{{transform:scale(2.8);opacity:0}}}}
.spin{{animation:spin 28s linear infinite;transform-box:fill-box;transform-origin:center}}.spinr{{animation:spin 40s linear infinite reverse;transform-box:fill-box;transform-origin:center}}@keyframes spin{{to{{transform:rotate(360deg)}}}}
.flow{{stroke-dasharray:4 7;animation:flow 1.4s linear infinite}}@keyframes flow{{to{{stroke-dashoffset:-22}}}}
.wave{{animation:wave 5s linear infinite}}@keyframes wave{{to{{transform:translateX(-240px)}}}}
.wave2{{animation:wave2 3s linear infinite}}@keyframes wave2{{to{{transform:translateX(-56px)}}}}
.scan{{animation:scan 3.6s linear infinite}}@keyframes scan{{from{{transform:translateX(0)}}to{{transform:translateX(168px)}}}}
.draw{{stroke-dasharray:420;animation:draw 5s ease-in-out infinite}}@keyframes draw{{0%{{stroke-dashoffset:420}}55%,85%{{stroke-dashoffset:0;opacity:1}}100%{{stroke-dashoffset:0;opacity:0}}}}
.twinkle{{animation:twinkle 2.2s ease-in-out infinite;transform-box:fill-box;transform-origin:center}}@keyframes twinkle{{0%,100%{{opacity:.15;transform:scale(.5)}}50%{{opacity:1;transform:scale(1)}}}}
.trip{{opacity:0;animation:trip 6s ease-in-out infinite}}@keyframes trip{{0%,12%{{opacity:0}}20%,72%{{opacity:1}}86%,100%{{opacity:0}}}}
.grow{{animation:grow 1.4s cubic-bezier(.2,.7,.2,1) both;transform-box:fill-box;transform-origin:left}}@keyframes grow{{from{{transform:scaleX(0)}}}}
.prog{{animation:prog 4.5s ease-in-out infinite;transform-box:fill-box;transform-origin:left}}@keyframes prog{{0%{{transform:scaleX(.04)}}80%,100%{{transform:scaleX(1)}}}}
.in{{animation:in .8s cubic-bezier(.2,.7,.2,1) both}}@keyframes in{{from{{opacity:0;transform:translateY(8px)}}}}
.pop{{animation:pop .5s ease-out both}}@keyframes pop{{from{{opacity:0}}}}
.sweep{{animation:sweep 6s ease-in-out infinite}}@keyframes sweep{{0%{{transform:translateX(-160px);opacity:0}}15%{{opacity:1}}60%,100%{{transform:translateX(1240px);opacity:0}}}}
@media(prefers-reduced-motion:reduce){{*{{animation:none!important}}.trip{{opacity:.8}}}}"""


# ---------------------------------------------------------------- helpers

def e(s):
    return escape(str(s), quote=True)


def tw(s, size, bold=False, mono=False, ls=0.0):
    """Estimated rendered width of s in px. No font metrics in an <img>, so stay generous."""
    s = s.replace("^{", "").replace("}", "")
    if mono:
        return len(s) * (0.57 * size + ls)
    w = 0.0
    for ch in s:
        if ch in "il.,:;'!|·":
            w += 0.26
        elif ch in "jtfI()[]r -/":
            w += 0.34
        elif ch in "mwMW":
            w += 0.86
        elif ch.isupper() or ch in "%&@$×~":
            w += 0.66
        elif ch.isdigit():
            w += 0.56
        else:
            w += 0.53
    return w * size * (1.07 if bold else 1.0) + ls * len(s)


def wrap(text, size, width, bold=False):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and tw(trial, size, bold) > width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def clip(s, n):
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[: n - 1].rstrip(" ,.;:·-") + "…"


def rich(value, size):
    """Text with one optional ^{...} superscript, as tspans."""
    m = re.search(r"\^\{(.*?)\}", value)
    if not m:
        return e(value)
    rest = e(value[m.end():]) or "&#8203;"
    return (f'{e(value[:m.start()])}<tspan dy="{-size * .42:.1f}" font-size="{size * .55:.1f}">{e(m.group(1))}</tspan>'
            f'<tspan dy="{size * .42:.1f}">{rest}</tspan>')


def day(iso):
    d = dt.date.fromisoformat(iso[:10])
    return f"{d.day} {d.strftime('%b %Y')}"


def svg(w, h, title, desc, body, rx=20):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" fill="none" '
            f'role="img" aria-labelledby="t d"><title id="t">{e(title)}</title><desc id="d">{e(desc)}</desc>'
            f'<defs><style>\n{CSS}\n</style><clipPath id="clip"><rect width="{w}" height="{h}" rx="{rx}"/></clipPath>'
            f'<pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.1" fill="#2a3530"/></pattern>'
            f'</defs><g clip-path="url(#clip)"><rect width="{w}" height="{h}" fill="{BG}"/>\n{body}\n</g>'
            f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{rx - .5}" stroke="{LINE}"/></svg>\n')


def write(name, content):
    ElementTree.fromstring(content)  # a malformed SVG renders as a broken image, so fail the run instead
    path = os.path.join(ASSETS, name)
    old = open(path, encoding="utf8").read() if os.path.exists(path) else None
    if content != old:
        with open(path, "w", encoding="utf8", newline="\n") as fh:
            fh.write(content)
        print(f"updated assets/{name}")


# ---------------------------------------------------------------- data

def fetch():
    body = json.dumps({"query": QUERY, "variables": {"login": USER}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}", "Content-Type": "application/json",
        "User-Agent": f"{USER}-profile"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    user = (data.get("data") or {}).get("user")
    if not user:
        raise SystemExit(f"GraphQL errors: {data.get('errors')}")
    if "errors" in data:  # e.g. a CI rollup the token may not read: build without it rather than not at all
        print(f"warning: partial GraphQL response: {data['errors']}")
    return user


def digest(user):
    repos = user["repositories"]["nodes"]
    pins = [p for p in user["pinnedItems"]["nodes"] if p]
    weeks = [w["contributionDays"] for w in user["contributionsCollection"]["contributionCalendar"]["weeks"]]
    days = [d for w in weeks for d in w]
    today = dt.date.fromisoformat(days[-1]["date"])  # "now" comes from the data, not the clock

    active = [r for r in pins if r["name"] not in SKIP] or [r for r in repos if r["name"] not in SKIP]
    building = max(active, key=lambda r: r["pushedAt"])
    released = [(r["latestRelease"]["publishedAt"], r["name"], r["latestRelease"]["tagName"])
                for r in repos if r["latestRelease"]]
    latest = max(released) if released else None

    langs = {}
    for r in repos:
        if r["name"] in SKIP or dt.date.fromisoformat(r["pushedAt"][:10]) < today - dt.timedelta(days=365):
            continue
        for edge in r["languages"]["edges"]:
            name = edge["node"]["name"]
            size, color = langs.get(name, (0, edge["node"]["color"] or MUTED))
            langs[name] = (size + edge["size"], color)
    return dict(
        pins=pins, building=building, latest=latest, weeks=weeks,
        repos=user["repositories"]["totalCount"], followers=user["followers"]["totalCount"],
        stars=sum(r["stargazerCount"] for r in repos),
        langs=sorted(langs.items(), key=lambda kv: -kv[1][0]),
    )


# ---------------------------------------------------------------- live: header

def header(d):
    W, H, bar = 1200, 400, 336
    b = d["building"]
    lr = d["latest"]
    logo = base64.b64encode(open(os.path.join(ASSETS, "logo-mark.jpg"), "rb").read()).decode()
    o = [f'<rect width="{W}" height="{bar}" fill="url(#dots)" opacity=".7"/>',
         '<radialGradient id="glow" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" '
         'gradientTransform="translate(1030 168) scale(330)"><stop stop-color="#48bfc4" stop-opacity=".16"/>'
         '<stop offset="1" stop-color="#48bfc4" stop-opacity="0"/></radialGradient>',
         f'<rect width="{W}" height="{bar}" fill="url(#glow)"/>']
    # three-phase 50 Hz motif, one period = 240 px, phases 120 degrees apart
    for i, col in enumerate((TEAL, SAGE, AMBER)):
        x0 = -240 - i * 80
        pts = " ".join(f"q60 {-26 if k % 2 == 0 else 26} 120 0" for k in range(17))
        o.append(f'<g opacity=".32"><path class="wave" d="M{x0} 308 {pts}" stroke="{col}" stroke-width="1.6"/></g>')
    o.append(f'<rect class="sweep" x="0" y="0" width="160" height="{bar}" fill="url(#sheen)"/>'
             '<linearGradient id="sheen" x1="0" x2="1"><stop stop-color="#fff" stop-opacity="0"/>'
             '<stop offset=".5" stop-color="#fff" stop-opacity=".035"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>')

    o.append(f'<g class="in"><text x="60" y="80" font-size="15" class="mono sage" letter-spacing="3">'
             f'ELECTRICAL &amp; ENERGY ENGINEERING · EHTP</text>'
             f'<text x="56" y="162" font-size="84" class="serif" letter-spacing="-2">Akeanti</text></g>')
    o.append(f'<g class="in" style="animation-delay:.15s"><text x="60" y="208" font-size="25" class="b">'
             f'Power systems · Embedded hardware · Scientific computing</text>'
             f'<text x="60" y="244" font-size="19" class="mu">First-year engineering student at EHTP, after CPGE MP · '
             f'Morocco · Arabic, French, English</text></g>')
    pill = "OPEN TO A FIRST-YEAR INTERNSHIP · SUMMER 2027 · 1–2 MONTHS"
    pw = tw(pill, 15, mono=True, ls=1.2) + 62
    o.append(f'<g class="in" style="animation-delay:.3s"><rect x="60" y="264" width="{pw:.0f}" height="40" rx="20" '
             f'fill="{BG}"/><rect x="60" y="264" width="{pw:.0f}" height="40" rx="20" fill="{SAGE}" fill-opacity=".1" '
             f'stroke="{SAGE}" stroke-opacity=".7"/><circle cx="84" cy="284" r="5" fill="{SAGE}"/>'
             f'<circle cx="84" cy="284" r="5" stroke="{SAGE}" class="ring"/>'
             f'<text x="100" y="289" font-size="15" class="mono sage b" letter-spacing="1.2">{pill}</text></g>')

    # logo with construction rings
    o.append(f'<circle cx="1030" cy="168" r="142" stroke="{LINE}" stroke-dasharray="2 8" class="spinr"/>'
             f'<g class="spin"><circle cx="1030" cy="168" r="124" stroke="{TEAL}" stroke-opacity=".55" '
             f'stroke-dasharray="70 40 8 40"/><circle cx="1154" cy="168" r="4.5" fill="{TEAL}"/><circle cx="906" cy="168" r="4.5" fill="none"/></g>'
             f'<clipPath id="lc"><circle cx="1030" cy="168" r="106"/></clipPath>'
             f'<image href="data:image/jpeg;base64,{logo}" x="924" y="62" width="212" height="212" clip-path="url(#lc)"/>'
             f'<circle cx="1030" cy="168" r="106" stroke="{LINE}" stroke-width="2"/>')

    # live status bar
    cy = bar + 37
    o.append(f'<rect y="{bar}" width="{W}" height="{H - bar}" fill="#121715"/><path d="M0 {bar}H{W}" stroke="{LINE}"/>')
    o.append(f'<circle cx="44" cy="{cy - 5}" r="5" fill="{TEAL}"/><circle cx="44" cy="{cy - 5}" r="5" stroke="{TEAL}" class="ring"/>'
             f'<text x="58" y="{cy}" font-size="13" class="mono teal b" letter-spacing="1.5">LIVE</text>')
    x = 112
    segs = [("NOW BUILDING", b["name"], f"pushed {day(b['pushedAt'])}")]
    if lr:
        segs.append(("LATEST RELEASE", f"{lr[1]} {lr[2]}", day(lr[0])))
    for label, value, extra in segs:
        o.append(f'<path d="M{x} {cy - 18}V{cy + 6}" stroke="{LINE}"/>')
        x += 22
        o.append(f'<text x="{x}" y="{cy}" font-size="12" class="mono mu" letter-spacing="1.5">{label}</text>')
        x += tw(label, 12, mono=True, ls=1.5) + 10
        o.append(f'<text x="{x:.0f}" y="{cy}" font-size="16" class="b">{e(value)}</text>')
        x += tw(value, 16, bold=True) + 9
        o.append(f'<text x="{x:.0f}" y="{cy}" font-size="15" class="dim">{e(extra)}</text>')
        x += tw(extra, 15) + 24
    right = "AUTO-UPDATED FROM GITHUB"
    if x + tw(right, 12, mono=True, ls=1.5) < W - 40:
        o.append(f'<text x="{W - 40}" y="{cy}" font-size="12" class="mono dim" text-anchor="end" letter-spacing="1.5">{right}</text>')

    desc = (f"Akeanti. Electrical and energy engineering student at EHTP, first year, after CPGE MP. Power systems, "
            f"embedded hardware and scientific computing. Open to a first-year internship, summer 2027, 1 to 2 months. "
            f"Now building: {b['name']}, pushed {day(b['pushedAt'])}."
            + (f" Latest release: {lr[1]} {lr[2]}, {day(lr[0])}." if lr else ""))
    return svg(W, H, "Akeanti", desc, "\n".join(o), rx=22)


# ---------------------------------------------------------------- live: pinned cards

def glyph(kind):
    """Small animated icon, drawn in a 52x52 box."""
    s = {"stroke": TEAL, "stroke-width": "2.2", "stroke-linecap": "round", "stroke-linejoin": "round"}
    a = " ".join(f'{k}="{v}"' for k, v in s.items())
    if kind == "bus":
        return (f'<path d="M15 17L37 17M15 17L26 37M37 17L26 37" {a} class="flow"/>'
                + "".join(f'<rect x="{x - 7}" y="{y - 2}" width="14" height="4" rx="1" fill="{SAGE}"/>' for x, y in ((15, 17), (37, 17), (26, 37))))
    if kind == "wave":
        return (f'<g clip-path="url(#gclip)"><g class="wave2"><path d="M0 26 q7 -14 14 0 t14 0 t14 0 t14 0 t14 0 t14 0 t14 0" {a}/></g></g>'
                f'<path d="M26 10V42" stroke="{SAGE}" stroke-width="1.6" stroke-dasharray="2 3" class="pulse"/>')
    if kind == "graph":
        nodes = [(14, 16), (38, 14), (26, 27), (14, 38), (38, 38)]
        edges = [(0, 2), (1, 2), (2, 3), (2, 4), (3, 4), (0, 1)]
        return ("".join(f'<path d="M{nodes[i][0]} {nodes[i][1]}L{nodes[j][0]} {nodes[j][1]}" stroke="{LINE}" stroke-width="2"/>' for i, j in edges)
                + "".join(f'<circle cx="{x}" cy="{y}" r="4.2" fill="{TEAL}"/>' for x, y in nodes)
                + "".join(f'<circle cx="{nodes[k][0]}" cy="{nodes[k][1]}" r="4.2" fill="{CORAL}" class="trip" style="animation-delay:{t}s"/>'
                          for k, t in ((2, 0), (4, .5), (3, 1))))
    if kind == "maze":
        return (f'<path d="M10 10H42V42H10Z M26 10V22 M10 26H20 M32 26V42" stroke="{DIM}" stroke-width="2"/>'
                f'<path d="M16 36 C16 28 22 30 24 22 S36 18 36 16" stroke="{SAGE}" stroke-width="2.4" stroke-linecap="round" class="draw" style="stroke-dasharray:60;animation-name:draws"/>'
                '<style>@keyframes draws{0%{stroke-dashoffset:60}55%,85%{stroke-dashoffset:0;opacity:1}100%{stroke-dashoffset:0;opacity:0}}</style>')
    if kind == "wand":
        return (f'<path d="M12 42L33 21" stroke="{TEXT}" stroke-width="3" stroke-linecap="round"/>'
                f'<path d="M12 42L17 37" stroke="{SAGE}" stroke-width="3.4" stroke-linecap="round"/>'
                + "".join(f'<path class="twinkle" style="animation-delay:{t}s" d="M{x} {y - r}L{x + r * .3} {y - r * .3}L{x + r} {y}L{x + r * .3} {y + r * .3}L{x} {y + r}L{x - r * .3} {y + r * .3}L{x - r} {y}L{x - r * .3} {y - r * .3}Z" fill="{c}"/>'
                          for x, y, r, c, t in ((38, 15, 6, TEAL, 0), (44, 27, 3.5, SAGE, .7), (27, 10, 3, AMBER, 1.3))))
    if kind == "presence":
        return (f'<rect x="9" y="12" width="34" height="28" rx="7" fill="#e16737"/>'
                f'<path d="M15 33 L21 24 L25 29 L30 19 L37 33" stroke="#fff" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>'
                f'<circle cx="41" cy="38" r="6.5" fill="{PANEL}"/><circle cx="41" cy="38" r="4" fill="#3ba55d" class="pulse"/>')
    return f'<path d="M20 18L12 26L20 34M32 18L40 26L32 34" {a}/>'


def art(kind):
    """Decorative animated vignette, drawn in a 170x72 box."""
    if kind == "oneline":
        buses = {"A": (12, 16), "B": (78, 10), "C": (150, 18), "D": (40, 56), "E": (110, 60), "F": (160, 52)}
        lines = [("A", "B"), ("B", "C"), ("A", "D"), ("D", "E"), ("B", "E"), ("C", "F"), ("E", "F")]
        o = [f'<path d="M{buses[a][0]} {buses[a][1]}L{buses[b][0]} {buses[b][1]}" stroke="{TEAL if (a, b) != ("B", "E") else AMBER}" '
             f'stroke-width="1.6" class="flow" style="animation-duration:{1.2 + i * .15:.2f}s"/>' for i, (a, b) in enumerate(lines)]
        o += [f'<rect x="{x - 11}" y="{y - 2.5}" width="22" height="5" rx="1.5" fill="{SAGE}"/>' for x, y in buses.values()]
        o.append(f'<circle cx="12" cy="34" r="7" stroke="{SAGE}" stroke-width="1.6"/><path d="M8 34q2 -4 4 0t4 0" stroke="{SAGE}" stroke-width="1.4"/>'
                 f'<path d="M12 27V19" stroke="{SAGE}" stroke-width="1.6"/>')
        return "".join(o)
    if kind == "wave":
        o = ['<clipPath id="ac"><rect width="170" height="72"/></clipPath><g clip-path="url(#ac)">']
        for col, ph, op in ((TEAL, 0, 1), (SAGE, 19, .55), (AMBER, 37, .4)):
            pts = " ".join(f"q14 {-24 if k % 2 == 0 else 24} 28 0" for k in range(16))
            o.append(f'<g class="wave2" style="animation-duration:{3 + ph / 20:.2f}s"><path d="M{-56 - ph} 36 {pts}" stroke="{col}" stroke-opacity="{op}" stroke-width="1.8"/></g>')
        o += [f'<path d="M{x} 4V68" stroke="{SAGE}" stroke-dasharray="2 4" class="pulse" style="animation-delay:{i * .6:.1f}s"/>' for i, x in enumerate((28, 84, 140))]
        o.append(f'<rect x="0" y="0" width="2" height="72" fill="{TEAL}" opacity=".8" class="scan"/></g>')
        return "".join(o)
    if kind == "cascade":
        nodes = [(10, 36), (42, 12), (46, 52), (80, 30), (112, 8), (116, 60), (146, 30), (166, 58), (166, 8)]
        edges = [(0, 1), (0, 2), (1, 3), (2, 3), (3, 4), (3, 5), (4, 6), (5, 6), (6, 7), (6, 8), (1, 4), (2, 5)]
        o = [f'<path d="M{nodes[i][0]} {nodes[i][1]}L{nodes[j][0]} {nodes[j][1]}" stroke="{LINE}" stroke-width="1.6"/>' for i, j in edges]
        o += [f'<path d="M{nodes[i][0]} {nodes[i][1]}L{nodes[j][0]} {nodes[j][1]}" stroke="{CORAL}" stroke-width="1.8" class="trip" style="animation-delay:{t}s"/>'
              for (i, j), t in (((3, 5), .3), ((5, 6), .8), ((6, 7), 1.3), ((2, 5), .6))]
        o += [f'<circle cx="{x}" cy="{y}" r="5" fill="{TEAL}"/>' for x, y in nodes]
        o += [f'<circle cx="{nodes[k][0]}" cy="{nodes[k][1]}" r="5" fill="{CORAL}" class="trip" style="animation-delay:{t}s"/>'
              for k, t in ((3, 0), (5, .5), (6, 1), (7, 1.5))]
        o.append(f'<circle cx="{nodes[3][0]}" cy="{nodes[3][1]}" r="5" stroke="{CORAL}" class="ring"/>')
        return "".join(o)
    if kind == "maze":
        o = []
        for i in range(8):
            for j in range(4):
                o.append(f'<rect x="{i * 24 - 1.5}" y="{j * 24 - 1.5}" width="3" height="3" fill="{DIM}"/>')
        # a solvable maze, and a run that rounds every corner instead of pivoting
        walls = ("M0 0H168 M0 72H168 M0 0V72 M168 0V72 M24 24V72 M24 24H48 M72 0V24 M72 24H96 "
                 "M48 48H120 M120 24V48 M144 24V72 M96 72V60")
        o.append(f'<path d="{walls}" stroke="{DIM}" stroke-width="1.6" stroke-opacity=".8"/>')
        o.append(f'<path d="M12 60V22Q12 12 22 12H50Q60 12 60 22V26Q60 36 70 36H98Q108 36 108 26V22Q108 12 118 12H146Q156 12 156 22V60" '
                 f'stroke="{SAGE}" stroke-width="2.6" stroke-linecap="round" class="draw"/>'
                 f'<circle cx="12" cy="60" r="4" fill="{TEAL}"/><rect x="150" y="54" width="12" height="12" rx="2" stroke="{AMBER}" stroke-width="1.6"/>')
        return "".join(o)
    if kind == "spell":
        o = [f'<path d="M6 66L40 40" stroke="{TEXT}" stroke-width="3" stroke-linecap="round"/>',
             f'<path d="M6 66L13 60" stroke="{SAGE}" stroke-width="3.4" stroke-linecap="round"/>',
             f'<path d="M48 58 L58 14 L84 46 L110 12 L122 58" stroke="{TEAL}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" class="draw"/>']
        for x, y, r, c, t in ((44, 36, 6, TEAL, 0), (140, 18, 5, SAGE, .6), (156, 46, 4, AMBER, 1.1), (100, 66, 3.5, SAGE, 1.6), (70, 8, 3.5, TEAL, .9)):
            o.append(f'<path class="twinkle" style="animation-delay:{t}s" d="M{x} {y - r}L{x + r * .3} {y - r * .3}L{x + r} {y}L{x + r * .3} {y + r * .3}'
                     f'L{x} {y + r}L{x - r * .3} {y + r * .3}L{x - r} {y}L{x - r * .3} {y - r * .3}Z" fill="{c}"/>')
        return "".join(o)
    if kind == "presence":
        return (f'<rect x="0" y="4" width="170" height="64" rx="10" fill="{CHIP}" stroke="{LINE}"/>'
                f'<rect x="12" y="16" width="40" height="40" rx="9" fill="#e16737"/>'
                f'<path d="M19 47 L26 34 L31 41 L37 27 L45 47" stroke="#fff" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round"/>'
                f'<circle cx="51" cy="54" r="7" fill="{CHIP}"/><circle cx="51" cy="54" r="4.5" fill="#3ba55d" class="pulse"/>'
                f'<text x="62" y="27" font-size="10.5" class="b">Simulating</text>'
                f'<text x="62" y="41" font-size="10" class="mu">motor_model.slx</text>'
                f'<rect x="62" y="48" width="96" height="5" rx="2.5" fill="{LINE}"/>'
                f'<rect x="62" y="48" width="96" height="5" rx="2.5" fill="{SAGE}" class="prog"/>')
    return ""


def card(repo):
    W, H = 520, 330
    p = PROJECTS.get(repo["name"], {})
    lang = repo["primaryLanguage"] or {}
    title = p.get("title", repo["name"])
    tag = p.get("tag", (lang.get("name") or "PROJECT").upper())
    pitch = p.get("pitch") or clip(repo["description"], 150)
    rel = repo["latestRelease"]
    stage = rel["tagName"] if rel else p.get("stage", "")
    ci = (((repo.get("defaultBranchRef") or {}).get("target") or {}).get("statusCheckRollup") or {}).get("state")

    o = [f'<rect width="{W}" height="{H}" fill="url(#dots)" opacity=".45"/>']
    tagw = tw(tag, 12, mono=True, ls=1.4) + 24
    o.append(f'<rect x="24" y="22" width="{tagw:.0f}" height="28" rx="14" fill="{SAGE}" fill-opacity=".08" stroke="{SAGE}" stroke-opacity=".45"/>'
             f'<text x="36" y="41" font-size="12" class="mono sage" letter-spacing="1.4">{e(tag)}</text>')
    x = W - 24
    if stage:
        sw = tw(stage, 12.5, mono=True, ls=1) + 24
        x -= sw
        if rel:
            o.append(f'<rect x="{x:.0f}" y="22" width="{sw:.0f}" height="28" rx="14" fill="{SAGE}"/>'
                     f'<text x="{x + sw / 2:.0f}" y="41" font-size="12.5" class="mono ink b" text-anchor="middle" letter-spacing="1">{e(stage)}</text>')
        else:
            col = AMBER if not stage.startswith("v") else SAGE
            o.append(f'<rect x="{x:.0f}" y="22" width="{sw:.0f}" height="28" rx="14" stroke="{col}" stroke-opacity=".75"/>'
                     f'<text x="{x + sw / 2:.0f}" y="41" font-size="12.5" class="mono b" text-anchor="middle" letter-spacing="1" style="fill:{col}">{e(stage)}</text>')
        x -= 14
    if ci:
        ok = ci == "SUCCESS"
        col, word = (SAGE, "CI PASSING") if ok else (AMBER, "CI RUNNING") if ci in ("PENDING", "EXPECTED") else (CORAL, "CI FAILING")
        cw = tw(word, 12, mono=True, ls=1.2)
        o.append(f'<text x="{x:.0f}" y="41" font-size="12" class="mono" text-anchor="end" letter-spacing="1.2" style="fill:{col}">{word}</text>'
                 f'<circle cx="{x - cw - 10:.0f}" cy="36" r="4" fill="{col}"/><circle cx="{x - cw - 10:.0f}" cy="36" r="4" stroke="{col}" class="ring"/>')

    o.append(f'<clipPath id="gclip"><rect width="52" height="52" rx="13"/></clipPath>'
             f'<g transform="translate(24 66)"><rect width="52" height="52" rx="13" fill="{CHIP}" stroke="{LINE}"/>{glyph(p.get("glyph", ""))}</g>')
    tsize = 28 if tw(title, 28, bold=True) < 230 else 24
    o.append(f'<text x="92" y="95" font-size="{tsize}" class="b" letter-spacing="-.5">{e(title)}</text>'
             f'<text x="92" y="116" font-size="13" class="mono dim">akeanti/{e(repo["name"])}</text>')
    title_end = max(92 + tw(title, tsize, bold=True), 92 + tw("akeanti/" + repo["name"], 13, mono=True))
    if p.get("art") and title_end < 316:
        o.append(f'<g transform="translate(326 60)" opacity=".9">{art(p["art"])}</g>')

    lines = wrap(pitch, 17, W - 48)
    if len(lines) > 3:
        print(f"warning: {repo['name']} pitch wraps to {len(lines)} lines")
    for i, line in enumerate(lines[:3]):
        o.append(f'<text x="24" y="{160 + i * 24}" font-size="17" class="mu">{e(line)}</text>')

    for i, (value, label) in enumerate(p.get("metrics", [])[:2]):
        mx = 24 + i * 248
        o.append(f'<g class="in" style="animation-delay:{.2 + i * .15:.2f}s"><text x="{mx}" y="252" font-size="27" class="b sage" letter-spacing="-.5">{rich(value, 27)}</text>'
                 f'<text x="{mx}" y="274" font-size="14" class="mu">{e(label)}</text></g>')
        if i == 0:
            o.append(f'<path d="M{mx + 232} 232V276" stroke="{LINE}"/>')

    o.append(f'<path d="M24 292H{W - 24}" stroke="{LINE}"/>')
    meta = f"★ {repo['stargazerCount']} · updated {day(repo['pushedAt'])}"
    o.append(f'<text x="{W - 24}" y="316" font-size="13.5" class="dim" text-anchor="end">{e(meta)}</text>')
    room = W - 48 - 18 - tw(meta, 13.5) - 10
    stack = p.get("stack") or lang.get("name") or ""
    parts = stack.split(" · ")
    while parts and tw(" · ".join(parts), 13.5, mono=True) > room:
        parts.pop()
    if lang.get("color"):
        o.append(f'<circle cx="30" cy="311" r="5" fill="{e(lang["color"])}"/>')
    o.append(f'<text x="42" y="316" font-size="13.5" class="mono mu">{e(" · ".join(parts))}</text>')

    metrics = "; ".join(f"{v.replace('^{', 'e').replace('}', '')} {l}" for v, l in p.get("metrics", []))
    desc = (f"{title}: {pitch} " + (f"Key numbers: {metrics}. " if metrics else "") + (f"Status: {stage}. " if stage else "")
            + (f"CI {ci.lower()}. " if ci else "") + f"{repo['stargazerCount']} stars, updated {day(repo['pushedAt'])}.")
    return svg(W, H, title, desc, "\n".join(o)), desc


# ---------------------------------------------------------------- live: stats

def stats(d):
    W, H = 1200, 250
    o = []
    weeks = 26
    cal = d["weeks"][-weeks:]
    recent = [x for w in cal for x in w]
    total = sum(x["contributionCount"] for x in recent)
    nz = sorted(x["contributionCount"] for x in recent if x["contributionCount"])
    qs = [nz[int(len(nz) * f)] for f in (.25, .5, .75)] if nz else [1, 2, 3]

    def level(c):
        return 0 if c == 0 else 1 + sum(c > q for q in qs)

    nums = [(total, "contributions", "last 26 weeks"), (d["repos"], "public repos", "on GitHub"),
            (d["stars"], "stars", "across my repos"), (d["followers"], "followers", "on GitHub")]
    o.append(f'<text x="36" y="50" font-size="12" class="mono sage" letter-spacing="2">GITHUB · LIVE</text>')
    for i, (v, a, b2) in enumerate(nums):
        x, y = 36 + (i % 2) * 170, 106 + (i // 2) * 86
        o.append(f'<g class="in" style="animation-delay:{i * .1:.1f}s"><text x="{x}" y="{y}" font-size="38" class="b" letter-spacing="-1">{v}</text>'
                 f'<text x="{x}" y="{y + 24}" font-size="14.5" class="mu">{a}</text>'
                 f'<text x="{x}" y="{y + 42}" font-size="12.5" class="dim">{b2}</text></g>')

    hx, hy, cell, gap = 400, 76, 13, 3
    o.append(f'<path d="M370 32V218" stroke="{LINE}"/><text x="{hx}" y="50" font-size="12" class="mono sage" letter-spacing="2">ACTIVITY · LAST 26 WEEKS</text>')
    last_month, last_label = None, -9
    for wk, week in enumerate(cal):
        cx = hx + wk * (cell + gap)
        for x in week:
            date = dt.date.fromisoformat(x["date"])
            cy = hy + ((date.weekday() + 1) % 7) * (cell + gap)  # Sunday on top, like GitHub
            o.append(f'<rect x="{cx}" y="{cy}" width="{cell}" height="{cell}" rx="3" fill="{HEAT[level(x["contributionCount"])]}" '
                     f'class="pop" style="animation-delay:{wk * .03:.2f}s"/>')
        month = week[0]["date"][:7]
        if month != last_month and wk - last_label >= 3 and wk < weeks - 2:
            o.append(f'<text x="{cx}" y="{hy + 7 * (cell + gap) + 14}" font-size="11.5" class="mono dim">'
                     f'{dt.date.fromisoformat(week[0]["date"]).strftime("%b")}</text>')
            last_label = wk
        last_month = month
    lx = hx + weeks * (cell + gap) - 3
    o.append(f'<text x="{lx - 5 * 16 - 8}" y="{hy - 10}" font-size="11.5" class="mono dim" text-anchor="end">less</text>')
    for i, c in enumerate(HEAT):
        o.append(f'<rect x="{lx - (5 - i) * 16 + 3}" y="{hy - 21}" width="11" height="11" rx="2.5" fill="{c}"/>')
    o.append(f'<text x="{lx + 6}" y="{hy - 10}" font-size="11.5" class="mono dim">more</text>')

    rx0, rw = 880, 284
    o.append(f'<path d="M850 32V218" stroke="{LINE}"/><text x="{rx0}" y="50" font-size="12" class="mono sage" letter-spacing="2">LANGUAGES · LAST 12 MONTHS</text>')
    top = d["langs"][:5]
    tot = sum(s for _, (s, _) in top) or 1
    x = rx0
    o.append(f'<clipPath id="bar"><rect x="{rx0}" y="72" width="{rw}" height="12" rx="6"/></clipPath><g clip-path="url(#bar)" class="grow">')
    for name, (size, color) in top:
        w = rw * size / tot
        o.append(f'<rect x="{x:.1f}" y="72" width="{w + .6:.1f}" height="12" fill="{e(color)}"/>')
        x += w
    o.append("</g>")
    for i, (name, (size, color)) in enumerate(top):
        y = 116 + i * 24
        o.append(f'<circle cx="{rx0 + 6}" cy="{y - 5}" r="5" fill="{e(color)}"/><text x="{rx0 + 20}" y="{y}" font-size="15">{e(name)}</text>'
                 f'<text x="{rx0 + rw}" y="{y}" font-size="14" class="mono mu" text-anchor="end">{100 * size / tot:.1f}%</text>')

    desc = (f"GitHub activity: {total} contributions in the last 26 weeks, {d['repos']} public repositories, {d['stars']} stars, "
            f"{d['followers']} followers. Languages over the last 12 months: "
            + ", ".join(f"{n} {100 * s / tot:.0f}%" for n, (s, _) in top) + ".")
    return svg(W, H, "GitHub activity", desc, "\n".join(o))


# ---------------------------------------------------------------- static

def kpis():
    W, H = 1200, 196
    tiles = [("10^{−13}", " pu", "match with the PYPOWER reference", "SWINGBUS", SAGE),
             ("8.3", " ms", "full N-1 screen of a 118-bus grid", "SWINGBUS", TEAL),
             ("2.4", "×", "faster maze runs with clothoid turns", "ARIADNE", SAGE),
             ("99.6", "%", "top-1 gesture recognition on-device", "MALFOID", TEAL),
             ("230", "+", "automated tests in CI across 4 repos", "4 REPOS", SAGE)]
    tw_ = (W - 48) / len(tiles)
    o = []
    for i, (num, unit, label, src, col) in enumerate(tiles):
        x = 24 + i * tw_ + 22
        if i:
            o.append(f'<path d="M{24 + i * tw_:.0f} 36V160" stroke="{LINE}"/>')
        o.append(f'<g class="in" style="animation-delay:{i * .12:.2f}s">'
                 f'<text x="{x:.0f}" y="52" font-size="12" class="mono" letter-spacing="2" style="fill:{col}">{src}</text>'
                 f'<text x="{x:.0f}" y="106" font-size="44" class="b" letter-spacing="-1.5">{rich(num, 44)}'
                 f'<tspan font-size="24" style="fill:{col}">{e(unit)}</tspan></text>')
        lines = wrap(label, 16, tw_ - 44)
        if len(lines) > 2:
            print(f"warning: kpi label wraps to {len(lines)} lines: {label}")
        for j, line in enumerate(lines[:2]):
            o.append(f'<text x="{x:.0f}" y="{138 + j * 21}" font-size="16" class="mu">{e(line)}</text>')
        o.append("</g>")
    desc = "Proof in numbers: " + "; ".join(f"{n.replace('^{', 'e').replace('}', '')}{u} {l} ({s.lower()})" for n, u, l, s, _ in tiles) + "."
    return svg(W, H, "Proof in numbers", desc, "\n".join(o))


def section(num, title, note):
    W, H = 1200, 76
    tx = 32 + tw(num, 14, mono=True, ls=2) + 18
    end = tx + tw(title, 30) + 26
    nx = W - 32 - tw(note, 12, mono=True, ls=1.6)
    o = [f'<text x="32" y="48" font-size="14" class="mono teal b" letter-spacing="2">{num}</text>',
         f'<text x="{tx:.0f}" y="49" font-size="30" class="serif" letter-spacing="-.6">{e(title)}</text>',
         f'<path d="M{end:.0f} 39H{nx - 22:.0f}" stroke="{LINE}"/>',
         f'<clipPath id="rule"><rect x="{end:.0f}" y="37" width="{nx - 22 - end:.0f}" height="4"/></clipPath>'
         f'<g clip-path="url(#rule)"><rect x="{end - 80:.0f}" y="38" width="80" height="2" fill="{TEAL}" class="scan" '
         f'style="animation-duration:5s;animation-name:rulescan"/></g>'
         f'<style>@keyframes rulescan{{from{{transform:translateX(0)}}to{{transform:translateX({nx - 22 - end + 80:.0f}px)}}}}</style>',
         f'<text x="{W - 32}" y="44" font-size="12" class="mono dim" text-anchor="end" letter-spacing="1.6">{e(note)}</text>']
    return svg(W, H, f"{num} {title}", f"{num} · {title}.", "\n".join(o), rx=18)


def skills():
    W = 1200
    cols = [("POWER & ENERGY", TEAL, ["Power flow (Newton-Raphson)", "N-1 contingency", "DC-OPF · LMPs", "Synchrophasors",
                                     "IEEE C37.118", "MATPOWER cases", "MATLAB · Simulink", "Signal processing"]),
            ("EMBEDDED & HARDWARE", SAGE, ["ESP32 · ESP32-S3", "ESP-IDF", "FreeRTOS", "C · C++", "PlatformIO", "KiCad",
                                          "IMU · sensors", "MQTT", "Arduino"]),
            ("SOFTWARE & DATA", AMBER, ["Python", "NumPy · SciPy", "PyTorch", "XGBoost · SHAP", "pytest", "Docker",
                                       "GitHub Actions", "Git · Linux", "LaTeX"])]
    cw, gap, pad, fs, ch = (W - 48 - 2 * 20) / 3, 20, 20, 15.5, 32
    blocks, height = [], 0
    for i, (title, col, chips) in enumerate(cols):
        x0 = 24 + i * (cw + gap)
        o = [f'<circle cx="{x0 + pad + 5:.0f}" cy="{44}" r="5" fill="{col}"/>'
             f'<text x="{x0 + pad + 18:.0f}" y="49" font-size="13" class="mono b" letter-spacing="2" style="fill:{col}">{e(title)}</text>']
        x, y = x0 + pad, 70
        for k, chip in enumerate(chips):
            w = tw(chip, fs) + 26
            if x + w > x0 + cw - pad:
                x, y = x0 + pad, y + ch + 9
            o.append(f'<g class="in" style="animation-delay:{i * .1 + k * .04:.2f}s"><rect x="{x:.0f}" y="{y}" width="{w:.0f}" height="{ch}" rx="9" fill="{CHIP}" stroke="{LINE}"/>'
                     f'<text x="{x + 13:.0f}" y="{y + 21.5}" font-size="{fs}">{e(chip)}</text></g>')
            x += w + 8
        height = max(height, y + ch + 22)
        blocks.append((x0, o))
    o = []
    for x0, inner in blocks:
        o.append(f'<rect x="{x0:.0f}" y="22" width="{cw:.0f}" height="{height - 22 - 2}" rx="14" fill="{PANEL}" stroke="{LINE}"/>')
        o += inner
    H = height + 22
    desc = "Toolkit. " + " ".join(f"{t.capitalize()}: {', '.join(c)}." for t, _, c in cols)
    return svg(W, H, "Toolkit", desc, "\n".join(o))


def button(label, icon, primary=False):
    W, H = 300, 64
    fg = INK if primary else TEXT
    fill = f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="31" fill="{SAGE}"/>' if primary else \
        f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="31" fill="{PANEL}" stroke="{LINE}" stroke-width="2"/>'
    st = f'stroke="{fg}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"'
    icons = {
        "cv": f'<path d="M-8 -11h11l6 6v16h-17z M3 -11v6h6 M-4 2h9 M-4 7h7" {st}/>',
        "mail": f'<rect x="-11" y="-8" width="22" height="16" rx="3" {st}/><path d="M-10 -6l10 7l10 -7" {st}/>',
        "web": f'<circle r="10.5" {st}/><path d="M-10.5 0h21 M0 -10.5c-6 6 -6 15 0 21 M0 -10.5c6 6 6 15 0 21" {st}/>',
        "grid": f'<rect x="-10" y="-10" width="8.5" height="8.5" rx="2" {st}/><rect x="1.5" y="-10" width="8.5" height="8.5" rx="2" {st}/>'
                f'<rect x="-10" y="1.5" width="8.5" height="8.5" rx="2" {st}/><rect x="1.5" y="1.5" width="8.5" height="8.5" rx="2" {st}/>',
    }
    lw = tw(label, 21, bold=True)
    x0 = (W - (lw + 34)) / 2
    body = (f'{fill}<g transform="translate({x0 + 11:.0f} 32)">{icons[icon]}</g>'
            f'<text x="{x0 + 34:.0f}" y="39.5" font-size="21" class="b" style="fill:{fg}">{e(label)}</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none" role="img" '
            f'aria-label="{e(label)}"><title>{e(label)}</title><defs><style>{CSS}</style></defs>{body}</svg>\n')


def contact():
    W, H = 1200, 310
    facts = [("WHEN", "Summer 2027", "1–2 months · dates on request"),
             ("WHERE", "Morocco or abroad", "on-site, hybrid or remote"),
             ("FIELDS", "Power & energy systems", "embedded · industrial AI · OT security"),
             ("SCHOOL", "EHTP · first year, GEE", "after CPGE MP and the CNC"),
             ("LANGUAGES", "Arabic · French · English", "native · fluent · professional"),
             ("CONTACT", "akeantie@gmail.com", "CV on request")]
    o = [f'<rect width="{W}" height="{H}" fill="url(#dots)" opacity=".6"/>',
         '<radialGradient id="cg" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(220 150) scale(420)">'
         '<stop stop-color="#b7cd91" stop-opacity=".12"/><stop offset="1" stop-color="#b7cd91" stop-opacity="0"/></radialGradient>'
         f'<rect width="{W}" height="{H}" fill="url(#cg)"/>',
         f'<text x="48" y="64" font-size="14" class="mono teal b" letter-spacing="2.5">03 · LET&#8217;S WORK TOGETHER</text>',
         f'<text x="46" y="128" font-size="44" class="serif" letter-spacing="-1">Hiring a first-year</text>',
         f'<text x="46" y="178" font-size="44" class="serif" letter-spacing="-1">engineering intern?</text>',
         f'<text x="48" y="214" font-size="17" class="mu">Stage de 1re année · summer 2027 · one click to start.</text>',
         f'<rect x="48" y="238" width="236" height="48" rx="24" fill="{SAGE}"/>'
         f'<text x="166" y="268" font-size="18" class="b ink" text-anchor="middle">Request my CV  →</text>',
         f'<rect x="618" y="30" width="556" height="{H - 60}" rx="16" fill="{PANEL}" stroke="{LINE}"/>']
    for i, (k, v, s) in enumerate(facts):
        x, y = 646 + (i % 2) * 270, 68 + (i // 2) * 76
        o.append(f'<g class="in" style="animation-delay:{i * .08:.2f}s"><text x="{x}" y="{y}" font-size="12" class="mono sage" letter-spacing="2">{k}</text>'
                 f'<text x="{x}" y="{y + 25}" font-size="17.5" class="b">{e(v)}</text>'
                 f'<text x="{x}" y="{y + 46}" font-size="14" class="mu">{e(s)}</text></g>')
    desc = ("Hiring a first-year engineering intern? Stage de 1re année, summer 2027. "
            + " ".join(f"{k.capitalize()}: {v}, {s}." for k, v, s in facts) + " Click to request my CV.")
    return svg(W, H, "Let's work together", desc, "\n".join(o), rx=22)


# ---------------------------------------------------------------- README pinned block

def readme_block(alts, pins):
    rows = []
    for i in range(0, len(pins), 2):
        cells = [f'  <a href="https://github.com/{USER}/{p["name"]}"><img src="./assets/pin-{i + j + 1}.svg" width="49%" alt="{e(alts[i + j])}"></a>'
                 for j, p in enumerate(pins[i:i + 2])]
        rows.append('<p align="center">\n' + "\n".join(cells) + "\n</p>")
    return "\n\n".join(rows)


def update_readme(block):
    text = open(README, encoding="utf8").read()
    new = re.sub(r"(<!-- PINNED:START[^>]*-->\n).*?(<!-- PINNED:END -->)", lambda m: m.group(1) + block + "\n" + m.group(2),
                 text, flags=re.S)
    if new != text:
        with open(README, "w", encoding="utf8", newline="\n") as fh:
            fh.write(new)
        print("updated README.md")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", help="build from a saved API response instead of fetching")
    ap.add_argument("--save", help="also save the API response here")
    args = ap.parse_args()
    if args.data:
        user = json.load(open(args.data, encoding="utf8"))
    else:
        user = fetch()
        if args.save:
            json.dump(user, open(args.save, "w", encoding="utf8"), indent=1)
    d = digest(user)

    write("header.svg", header(d))
    write("stats.svg", stats(d))
    alts = []
    for i, repo in enumerate(d["pins"], 1):
        content, alt = card(repo)
        write(f"pin-{i}.svg", content)
        alts.append(alt)
    for i in range(len(d["pins"]) + 1, 7):
        path = os.path.join(ASSETS, f"pin-{i}.svg")
        if os.path.exists(path):
            os.remove(path)
            print(f"removed assets/pin-{i}.svg")
    update_readme(readme_block(alts, d["pins"]))

    write("kpis.svg", kpis())
    write("skills.svg", skills())
    write("section-work.svg", section("01", "Featured work", "MIRRORS MY GITHUB PINS · LIVE CI"))
    write("section-toolkit.svg", section("02", "Toolkit & activity", "WHAT I WORK WITH"))
    write("contact.svg", contact())
    write("btn-cv.svg", button("Request CV", "cv", primary=True))
    write("btn-email.svg", button("Email me", "mail"))
    write("btn-site.svg", button("akeanti.xyz", "web"))
    write("btn-work.svg", button("See projects", "grid"))


if __name__ == "__main__":
    main()
