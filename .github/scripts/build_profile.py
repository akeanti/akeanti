#!/usr/bin/env python3
"""Build every SVG on the profile, and the pinned-projects block of README.md, from the GitHub API.

Run by .github/workflows/profile.yml every six hours. Standard library only.

    GITHUB_TOKEN=... python .github/scripts/build_profile.py            # fetch, then build
    python .github/scripts/build_profile.py --data snapshot.json        # build from a saved response
    GITHUB_TOKEN=... python .github/scripts/build_profile.py --save snapshot.json

Every graphic uses the logo's own palette (its charcoal, white, teal and sage) and the look of an
engineering drawing sheet: hairlines, figure plates, serif for display, mono for data.

Live:   header (now building, latest release), pin-N (one card per GitHub pin, in pin order, with
        release, CI state, stars and last push), stats (weekly activity, languages).
Static: kpis, tipe, background, skills, section-*, btn-*, contact.
        Their facts come from my CV (cv/Elmehdi_Essamit_CV.pdf); keep the two in step.

Outputs depend only on GitHub data, never on the wall clock, so the workflow commits only when
something changed: a push, a release, a star, a new pin, or another day of contributions.
"""
import argparse
import base64
import datetime as dt
import json
import math
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

NAME = "Elmehdi Essamit"
EMAIL = "essamit.elmehdi@proton.me"
SITE = "elmehdi-essamit.com"
LINKEDIN = "linkedin.com/in/elmehdi-essamit"

# Sampled from assets/logo.jpg: its background, white, teal and sage. Nothing else.
LOGO = dict(paper="#1A1C1B", frame="#323634", minor="#202322", major="#272B29", ink="#F6F6F4",
            body="#C8CDCA", soft="#8E9692", faint="#5C635F", rule="#2A2E2C", teal="#42BBC4", sage="#93B787")

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
        kind="Machine learning for power grids", stage="v0.3", art="cascade",
        pitch="Early warning for cascading grid failures: five graph neural networks against XGBoost "
              "on PowerGraph (NeurIPS 2024), with edge attributions you can check.",
        metrics=[("5 GNNs", "against tuned XGBoost baselines"), ("3 splits", "leakage-checked evaluation")],
        stack="PyTorch · XGBoost · Streamlit · Docker"),
    "swingbus": dict(
        kind="Power systems analysis", stage="v0.1", art="oneline",
        pitch="Power flow, N-1 contingency screening and DC optimal power flow with LMPs for "
              "transmission grids, in about 3,000 lines of NumPy and SciPy.",
        metrics=[("10^{−13} pu", "agreement with PYPOWER"), ("8.3 ms", "full N-1 screen, 118 buses")],
        stack="Python · NumPy · SciPy · mypy strict"),
    "nabd": dict(
        kind="Grid sensing hardware", stage="pre-release", art="scope",
        pitch="Open network of GPS-synchronized ESP32-S3 nodes measuring grid frequency, ROCOF and "
              "synchrophasors (IEEE C37.118), with a live map and open data.",
        metrics=[("$59", "per node, bill of materials"), ("C37.118", "IEEE synchrophasor format")],
        stack="C · ESP-IDF · Python · TypeScript · KiCad"),
    "matlab-discord-rpc": dict(
        title="drpc", kind="Developer tools", art="presence",
        pitch="Discord Rich Presence for MATLAB and Simulink: shows what you are editing, running, "
              "debugging or simulating. Runs inside MATLAB, no Python or Node.",
        metrics=[("9", "activity states detected"), ("1 line", "install from MATLAB")],
        stack="MATLAB · C# · .NET · Windows"),
    "ariadne": dict(
        kind="Robotics and control", art="maze",
        pitch="Simulation-first ESP32 micromouse: clothoid turn synthesis, time-optimal planning and "
              "a 10 kHz physics model running the real firmware control law.",
        metrics=[("2.4×", "faster than stop-and-pivot"), ("115", "automated tests in CI")],
        stack="C++ · Python · FreeRTOS · ESP32"),
    "malfoid": dict(
        kind="Embedded systems", stage="active build", art="spell",
        pitch="ESP32-S3 gesture wand: on-device spell recognition from a 6-axis IMU, haptics, and "
              "smart-home control through Home Assistant and MQTT.",
        metrics=[("99.6%", "top-1 accuracy on test casts"), ("~1 ms", "inference on the ESP32-S3")],
        stack="C++ · ESP32-S3 · MQTT · Web Serial"),
}

SANS = "Inter,'Segoe UI',-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif"
SERIF = "'Iowan Old Style','Palatino Linotype',Palatino,'Book Antiqua',Georgia,serif"
MONO = "'JetBrains Mono','SF Mono','Cascadia Mono',Consolas,Menlo,monospace"


def css(t):
    return f"""text{{font-family:{SANS};fill:{t['ink']}}}.serif{{font-family:{SERIF}}}.mono{{font-family:{MONO}}}
.b{{font-weight:600}}.it{{font-style:italic}}.body{{fill:{t['body']}}}.soft{{fill:{t['soft']}}}.faint{{fill:{t['faint']}}}
.teal{{fill:{t['teal']}}}.sage{{fill:{t['sage']}}}.paper{{fill:{t['paper']}}}
.ring{{animation:ring 2.6s ease-out infinite;transform-box:fill-box;transform-origin:center}}@keyframes ring{{0%{{transform:scale(1);opacity:.7}}100%{{transform:scale(3.4);opacity:0}}}}
.flow{{stroke-dasharray:1.5 9;animation:flow 1.1s linear infinite}}@keyframes flow{{to{{stroke-dashoffset:-21}}}}
.draw{{stroke-dasharray:440;animation:draw 6s cubic-bezier(.45,0,.2,1) infinite}}@keyframes draw{{0%{{stroke-dashoffset:440}}55%,88%{{stroke-dashoffset:0;opacity:1}}100%{{stroke-dashoffset:0;opacity:0}}}}
.trip{{opacity:0;animation:trip 7s ease-in-out infinite}}@keyframes trip{{0%,10%{{opacity:0}}18%,72%{{opacity:1}}86%,100%{{opacity:0}}}}
.bar{{animation:bar 1.1s cubic-bezier(.2,.7,.2,1) both;transform-box:fill-box;transform-origin:bottom}}@keyframes bar{{from{{transform:scaleY(0)}}}}
.grow{{animation:grow 1.2s cubic-bezier(.2,.7,.2,1) both;transform-box:fill-box;transform-origin:left}}@keyframes grow{{from{{transform:scaleX(0)}}}}
.prog{{animation:prog 4.5s ease-in-out infinite;transform-box:fill-box;transform-origin:left}}@keyframes prog{{0%{{transform:scaleX(.05)}}80%,100%{{transform:scaleX(1)}}}}
.blink{{animation:blink 2.4s ease-in-out infinite}}@keyframes blink{{0%,100%{{opacity:.3}}50%{{opacity:1}}}}
.twinkle{{animation:twinkle 2.4s ease-in-out infinite;transform-box:fill-box;transform-origin:center}}@keyframes twinkle{{0%,100%{{opacity:.2;transform:scale(.5)}}50%{{opacity:1;transform:scale(1)}}}}
@media(prefers-reduced-motion:reduce){{*{{animation:none!important}}}}"""


# ---------------------------------------------------------------- helpers

def e(s):
    return escape(str(s), quote=True)


def tw(s, size, bold=False, mono=False, serif=False, ls=0.0):
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
    return w * size * (1.07 if bold else 1.0) * (1.05 if serif else 1.0) + ls * len(s)


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


def plain(value):
    return re.sub(r"10\^\{−(\d+)\}", lambda m: f"1e-{m.group(1)}", value)


def day(iso):
    d = dt.date.fromisoformat(iso[:10])
    return f"{d.day} {d.strftime('%b %Y')}"


def svg(t, w, h, title, desc, body, card=True, defs=""):
    bg = f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="4" fill="{t["paper"]}" stroke="{t["frame"]}"/>' if card else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" fill="none" '
            f'role="img" aria-labelledby="t d"><title id="t">{e(title)}</title><desc id="d">{e(desc)}</desc>'
            f'<defs><style>\n{css(t)}\n</style>{defs}</defs>{bg}\n{body}\n</svg>\n')


def graph_paper(t, pid="gp"):
    return (f'<pattern id="{pid}" width="50" height="50" patternUnits="userSpaceOnUse">'
            f'<path d="M10 0V50M20 0V50M30 0V50M40 0V50M0 10H50M0 20H50M0 30H50M0 40H50" stroke="{t["minor"]}"/>'
            f'<path d="M.5 0V50M0 .5H50" stroke="{t["major"]}"/></pattern>')


def star(x, y, r):
    k = r * .28
    return (f"M{x} {y - r}L{x + k} {y - k}L{x + r} {y}L{x + k} {y + k}L{x} {y + r}L{x - k} {y + k}"
            f"L{x - r} {y}L{x - k} {y - k}Z")


def write(name, content):
    ElementTree.fromstring(content)  # a malformed SVG renders as a broken image, so fail the run instead
    path = os.path.join(ASSETS, name)
    old = open(path, encoding="utf8").read() if os.path.exists(path) else None
    if content != old:
        with open(path, "w", encoding="utf8", newline="\n") as fh:
            fh.write(content)
        print(f"updated assets/{name}")


def emit(name, draw, *args):
    write(f"{name}.svg", draw(LOGO, *args))


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
    today = dt.date.fromisoformat(weeks[-1][-1]["date"])  # "now" comes from the data, not the clock

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
            langs[edge["node"]["name"]] = langs.get(edge["node"]["name"], 0) + edge["size"]
    return dict(
        pins=pins, building=building, latest=latest, weeks=weeks,
        revision=max(r["pushedAt"] for r in active)[:7].replace("-", "."),
        repos=user["repositories"]["totalCount"], followers=user["followers"]["totalCount"],
        stars=sum(r["stargazerCount"] for r in repos),
        langs=sorted(langs.items(), key=lambda kv: -kv[1]),
    )


# ---------------------------------------------------------------- header: a drawing sheet with live phasors

def header(t, d):
    W, H, m = 1200, 420, 14
    o = [f'<rect x="{m}" y="{m}" width="{W - 2 * m}" height="{H - 2 * m}" stroke="{t["frame"]}"/>']
    # zone marks in the sheet margin, as on a drawing
    zw, zh = (W - 2 * m) / 6, (H - 2 * m) / 2
    for i in range(6):
        x = m + zw * (i + .5)
        o.append(f'<text x="{x:.0f}" y="10.5" font-size="8.5" class="mono faint" text-anchor="middle">{i + 1}</text>'
                 f'<text x="{x:.0f}" y="{H - 4}" font-size="8.5" class="mono faint" text-anchor="middle">{i + 1}</text>')
        if i:
            xb = m + zw * i
            o.append(f'<path d="M{xb:.0f} 6V{m}M{xb:.0f} {H - m}V{H - 6}" stroke="{t["frame"]}"/>')
    for j, letter in enumerate("AB"):
        y = m + zh * (j + .5) + 3
        o.append(f'<text x="7" y="{y:.0f}" font-size="8.5" class="mono faint" text-anchor="middle">{letter}</text>'
                 f'<text x="{W - 7}" y="{y:.0f}" font-size="8.5" class="mono faint" text-anchor="middle">{letter}</text>')
    o.append(f'<path d="M6 {m + zh:.0f}H{m}M{W - m} {m + zh:.0f}H{W - 6}" stroke="{t["frame"]}"/>')

    # identity
    first, last = NAME.split()
    nsize = 80 if tw(NAME, 80, serif=True) < 660 else 68
    o.append(f'<text x="56" y="82" font-size="17" class="serif it soft">Élève-ingénieur, first year · Electrical and energy engineering · EHTP</text>'
             f'<text x="52" y="164" font-size="{nsize}" class="serif" letter-spacing="-1.5">{e(first)} <tspan class="teal">{e(last)}</tspan></text>')
    lede = "Power grids, energy and embedded systems."
    size = 22 if tw(lede, 22) < 660 else 20
    pitch = "From the ESP32 sensor to the grid solver, every result checked against a reference."
    psize = 16.5 if tw(pitch, 16.5) < 660 else 15.5
    o.append(f'<text x="56" y="212" font-size="{size}" class="body">{lede}</text>'
             f'<text x="56" y="244" font-size="{psize}" class="soft">{pitch}</text>')
    o.append(f'<circle cx="62" cy="285" r="4.5" fill="{t["teal"]}"/><circle cx="62" cy="285" r="4.5" stroke="{t["teal"]}" class="ring"/>'
             f'<text x="78" y="291" font-size="17" class="b">Open to a first-year internship, summer 2027, for 1 to 2 months</text>')

    # my portrait at the centre of a phasor ring: three phases in the logo's white, teal and sage
    # orbit it, and each one draws its own waveform to the left
    cx, cy, R, T, lam = 1030, 170, 108, 9, 150
    x0, xl = cx - R - 30, 742
    phases = [(90, t["ink"]), (-30, t["teal"]), (210, t["sage"])]
    logo = base64.b64encode(open(os.path.join(ASSETS, "logo-mark.jpg"), "rb").read()).decode()
    photo = base64.b64encode(open(os.path.join(ASSETS, "photo.jpg"), "rb").read()).decode()
    pr = R - 12
    o.append(f'<path d="M{xl} {cy}H{cx - R - 14}M{cx + R + 14} {cy}H{cx + R + 26}" stroke="{t["frame"]}"/>'
             f'<path d="M{cx} {cy - R - 26}V{cy - R - 14}M{cx} {cy + R + 14}V{cy + R + 20}" stroke="{t["frame"]}"/>'
             f'<path d="M{x0} {cy - R - 6}V{cy + R + 6}" stroke="{t["frame"]}" stroke-dasharray="2 4"/>'
             f'<circle cx="{cx}" cy="{cy}" r="{R}" stroke="{t["frame"]}"/>'
             f'<clipPath id="pf"><circle cx="{cx}" cy="{cy}" r="{pr}"/></clipPath>'
             f'<image href="data:image/jpeg;base64,{photo}" x="{cx - pr}" y="{cy - pr}" width="{2 * pr}" height="{2 * pr}" clip-path="url(#pf)"/>'
             f'<circle cx="{cx}" cy="{cy}" r="{pr}" stroke="{t["frame"]}" stroke-width="2"/>')
    for a in range(0, 360, 15):
        r1, r2 = R + 4, R + (12 if a % 90 == 0 else 8 if a % 30 == 0 else 6)
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        o.append(f'<path d="M{cx + r1 * c:.1f} {cy - r1 * s:.1f}L{cx + r2 * c:.1f} {cy - r2 * s:.1f}" stroke="{t["faint"] if a % 30 == 0 else t["frame"]}"/>')
    o.append(f'<clipPath id="wv"><rect x="{xl}" y="{cy - R - 10}" width="{x0 - xl}" height="{2 * R + 20}"/></clipPath>'
             f'<style>.slide{{animation:slide {T}s linear infinite}}@keyframes slide{{to{{transform:translateX(-{lam}px)}}}}'
             f'.ccw{{animation:ccw {T}s linear infinite;transform-box:view-box;transform-origin:{cx}px {cy}px}}'
             f'@keyframes ccw{{to{{transform:rotate(-360deg)}}}}</style>')
    for k, (phi, col) in enumerate(phases):
        p = math.radians(phi)
        pts = " ".join(f"{x},{cy - R * math.sin(p + 2 * math.pi * (x - x0) / lam):.1f}" for x in range(xl, x0 + lam + 1, 2))
        o.append(f'<g clip-path="url(#wv)"><g class="slide"><polyline points="{pts}" stroke="{col}" stroke-width="1.5"/></g></g>')
        steps = 36
        frames = "".join(f"{100 * i / steps:.2f}%{{transform:translateY({-R * math.sin(p + 2 * math.pi * i / steps):.1f}px)}}" for i in range(steps + 1))
        o.append(f'<style>@keyframes head{k}{{{frames}}}.head{k}{{animation:head{k} {T}s linear infinite}}</style>'
                 f'<circle cx="{x0}" cy="{cy}" r="3.2" fill="{col}" class="head{k}"/>')
    rot = []
    for phi, col in phases:
        p, q = math.radians(phi), math.radians(phi - 40)
        tx, ty = cx + R * math.cos(p), cy - R * math.sin(p)
        # a short trail behind each phase, then the phase itself
        rot.append(f'<path d="M{cx + R * math.cos(q):.1f} {cy - R * math.sin(q):.1f}A{R} {R} 0 0 0 {tx:.1f} {ty:.1f}" '
                   f'stroke="{col}" stroke-width="2" stroke-opacity=".55" stroke-linecap="round"/>'
                   f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="7" fill="{col}" fill-opacity=".16"/>'
                   f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="3.8" fill="{col}"/>')
    o.append(f'<g class="ccw">{"".join(rot)}</g>')
    o.append(f'<text x="{cx}" y="{cy + R + 38}" font-size="13.5" class="serif it soft" text-anchor="middle">Fig. 1. Three phases, 120° apart</text>'
             f'<text x="{xl}" y="{cy - R - 14}" font-size="13.5" class="serif it soft">v(t)</text>')

    # title block, live from GitHub
    b, lr = d["building"], d["latest"]
    top = 330
    cells = [("NOW BUILDING", b["name"], f"last push {day(b['pushedAt'])}"),
             ("LATEST RELEASE", f"{lr[1]} {lr[2]}" if lr else "none yet", day(lr[0]) if lr else ""),
             ("BASED IN", "Casablanca, Morocco", "UTC+1"),
             ("SHEET", f"EE-01 · rev {d['revision']}", "rebuilt every 6 h")]
    bounds = [m, 340, 640, 920, W - m]
    o.append(f'<path d="M{m} {top}H{W - m}" stroke="{t["frame"]}"/>')
    for i, (label, value, sub) in enumerate(cells):
        x = bounds[i] + (42 if i == 0 else 24)
        if i:
            o.append(f'<path d="M{bounds[i]} {top}V{H - m}" stroke="{t["frame"]}"/>')
        if label == "SHEET":
            o.append(f'<image href="data:image/jpeg;base64,{logo}" x="{bounds[i] + 14}" y="{top + 10}" width="56" height="56"/>')
            x = bounds[i] + 80
        o.append(f'<text x="{x}" y="{top + 22}" font-size="10" class="mono soft" letter-spacing="1.6">{label}</text>'
                 f'<text x="{x}" y="{top + 46}" font-size="17" class="b">{e(value)}</text>'
                 f'<text x="{x}" y="{top + 66}" font-size="13" class="soft">{e(sub)}</text>')

    desc = (f"{NAME} (akeanti). Electrical and energy engineering student at EHTP, first year, based in Casablanca. "
            f"Power grids, energy and embedded systems. {pitch} Open to a first-year internship, summer 2027, for 1 to 2 months. "
            f"Now building: {b['name']}, last push {day(b['pushedAt'])}."
            + (f" Latest release: {lr[1]} {lr[2]}, {day(lr[0])}." if lr else "")
            + " Illustration: a portrait of me inside a ring of three rotating phasors drawing their sine waves.")
    return svg(t, W, H, NAME, desc, "\n".join(o))


# ---------------------------------------------------------------- pinned cards

def art(t, kind):
    """Line drawing for a card's figure plate, in a 300x88 box."""
    ink, teal, sage, soft, frame, paper = t["ink"], t["teal"], t["sage"], t["soft"], t["frame"], t["paper"]
    if kind == "oneline":  # single-line diagram: generator, transformer, four buses, one loaded line
        lines = ["M24 46H46", "M46 30H66", "M90 30H112", "M46 64H176", "M112 44H140V56H176", "M240 38H208V70H176"]
        o = [f'<path d="{p}" stroke="{ink}" stroke-width="1.4"/>' for p in lines]
        o += [f'<path d="{p}" stroke="{teal}" stroke-width="1.6" class="flow" style="animation-duration:{1 + i * .12:.2f}s"/>'
              for i, p in enumerate(lines[3:])]
        o.append(f'<path d="M112 22H240" stroke="{teal}" stroke-width="2"/>'
                 f'<text x="176" y="17" font-size="9" class="mono teal" text-anchor="middle">100%</text>')
        o += [f'<path d="M{x} {y1}V{y2}" stroke="{ink}" stroke-width="4"/>' for x, y1, y2 in ((46, 20, 72), (112, 14, 50), (176, 50, 80), (240, 10, 44))]
        o += [f'<text x="{x}" y="{y}" font-size="9" class="mono soft">{n}</text>' for x, y, n in ((50, 18, 1), (116, 12, 2), (180, 48, 3), (244, 8, 4))]
        o.append(f'<circle cx="14" cy="46" r="10" stroke="{ink}" stroke-width="1.4" fill="{paper}"/>'
                 f'<path d="M8.5 46q2.75 -5 5.5 0t5.5 0" stroke="{ink}" stroke-width="1.3"/>'
                 f'<circle cx="73" cy="30" r="7" stroke="{ink}" stroke-width="1.4"/><circle cx="83" cy="30" r="7" stroke="{ink}" stroke-width="1.4"/>'
                 f'<path d="M240 28H282" stroke="{ink}" stroke-width="1.4"/><path d="M282 23L292 28L282 33Z" fill="{ink}"/>')
        return "".join(o)
    if kind == "scope":  # mains waveform, sampled, against GPS pulse-per-second marks
        lam = 75
        pts = " ".join(f"{x},{42 - 24 * math.sin(2 * math.pi * x / lam):.1f}" for x in range(0, 300 + lam + 1, 2))
        dots = "".join(f'<circle cx="{x}" cy="{42 - 24 * math.sin(2 * math.pi * x / lam):.1f}" r="2.2" fill="{sage}"/>'
                       for x in [i * 12.5 for i in range(0, 31)])
        return (f'<clipPath id="sc"><rect width="300" height="88"/></clipPath><path d="M0 42H300" stroke="{frame}"/>'
                f'<style>.mv{{animation:mv 3.2s linear infinite}}@keyframes mv{{to{{transform:translateX(-{lam}px)}}}}</style>'
                f'<g clip-path="url(#sc)"><g class="mv"><polyline points="{pts}" stroke="{ink}" stroke-width="1.5"/>{dots}</g></g>'
                + "".join(f'<path d="M{x} 74V86" stroke="{teal}" stroke-width="1.6" class="blink" style="animation-delay:{i * .6:.1f}s"/>'
                          for i, x in enumerate((20, 95, 170, 245)))
                + f'<text x="252" y="84" font-size="9" class="mono teal">PPS</text>')
    if kind == "cascade":  # an outage propagating through the network
        nodes = [(10, 44), (52, 14), (56, 70), (104, 40), (150, 10), (156, 74), (200, 40), (246, 14), (250, 70), (292, 42)]
        edges = [(0, 1), (0, 2), (1, 3), (2, 3), (1, 4), (3, 4), (3, 5), (2, 5), (4, 6), (5, 6), (6, 7), (6, 8), (7, 9), (8, 9), (4, 7), (5, 8)]
        trips = [((3, 5), .2), ((5, 6), .7), ((6, 8), 1.2), ((8, 9), 1.7), ((5, 8), 1.4)]
        o = [f'<path d="M{nodes[i][0]} {nodes[i][1]}L{nodes[j][0]} {nodes[j][1]}" stroke="{soft}" stroke-width="1.1"/>' for i, j in edges]
        o += [f'<path d="M{nodes[i][0]} {nodes[i][1]}L{nodes[j][0]} {nodes[j][1]}" stroke="{teal}" stroke-width="2" class="trip" style="animation-delay:{s}s"/>' for (i, j), s in trips]
        o += [f'<circle cx="{x}" cy="{y}" r="4.6" fill="{paper}" stroke="{ink}" stroke-width="1.4"/>' for x, y in nodes]
        o += [f'<circle cx="{nodes[k][0]}" cy="{nodes[k][1]}" r="4.6" fill="{teal}" class="trip" style="animation-delay:{s}s"/>'
              for k, s in ((5, .2), (6, .7), (8, 1.2), (9, 1.7))]
        mx, my = (nodes[3][0] + nodes[5][0]) / 2, (nodes[3][1] + nodes[5][1]) / 2
        o.append(f'<path d="M{mx - 4} {my - 4}l8 8m0 -8l-8 8" stroke="{teal}" stroke-width="1.8"/>')
        return "".join(o)
    if kind == "maze":  # a solvable maze and a run that rounds every corner
        walls = ("M0 0H288V72H0Z M24 24V72 M24 24H72 M96 0V24 M96 24H144 M24 48H216 M168 24V48 M168 24H216 "
                 "M240 0V48 M264 24H288 M264 24V48 M120 48V72 M192 48V72")
        o = [f'<g transform="translate(6 8)"><path d="{walls}" stroke="{ink}" stroke-width="1.5"/>']
        o += [f'<rect x="{i * 24 - 1.5}" y="{j * 24 - 1.5}" width="3" height="3" fill="{ink}"/>' for i in range(13) for j in range(4)]
        o.append(f'<path d="M12 60V22Q12 12 22 12H74Q84 12 84 22V26Q84 36 94 36H146Q156 36 156 26V22Q156 12 166 12H218Q228 12 228 22V50Q228 60 238 60H276" '
                 f'stroke="{teal}" stroke-width="2.2" stroke-linecap="round" class="draw"/>'
                 f'<circle cx="12" cy="60" r="4" fill="{sage}"/><rect x="270" y="54" width="12" height="12" stroke="{ink}" stroke-width="1.4"/></g>')
        return "".join(o)
    if kind == "spell":  # a drawn "M", resampled to 32 points as the recognizer sees it
        poly = [(84, 76), (104, 14), (140, 58), (176, 14), (196, 76)]
        seg = [math.dist(poly[i], poly[i + 1]) for i in range(len(poly) - 1)]
        total, pts = sum(seg), []
        for k in range(32):
            s, i = total * k / 31, 0
            while i < len(seg) - 1 and s > seg[i]:
                s -= seg[i]
                i += 1
            f = min(s / seg[i], 1)
            pts.append((poly[i][0] + f * (poly[i + 1][0] - poly[i][0]), poly[i][1] + f * (poly[i + 1][1] - poly[i][1])))
        o = [f'<path d="M14 82L58 50" stroke="{ink}" stroke-width="3" stroke-linecap="round"/><path d="M14 82L22 76" stroke="{teal}" stroke-width="3.4" stroke-linecap="round"/>',
             f'<path class="twinkle" d="{star(62, 46, 6)}" fill="{sage}"/>',
             f'<path d="M84 76C92 52 98 30 104 14C116 30 128 44 140 58C152 44 164 30 176 14C182 30 188 52 196 76" stroke="{teal}" stroke-width="2.2" stroke-linecap="round" class="draw"/>']
        o += [f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.7" fill="{ink}"/>' for x, y in pts]
        o.append(f'<text x="214" y="36" font-size="9" class="mono soft">32 points</text><text x="214" y="50" font-size="9" class="mono soft">DTW match</text>'
                 f'<text x="214" y="70" font-size="12" class="serif it teal">"Malfoid"</text>')
        return "".join(o)
    if kind == "presence":  # the Discord card drpc produces
        return (f'<text x="0" y="30" font-size="10" class="mono soft">&gt;&gt; drpc start</text>'
                f'<text x="0" y="46" font-size="10" class="mono teal">connected</text>'
                f'<rect x="96" y="6" width="204" height="76" rx="5" fill="{paper}" stroke="{frame}"/>'
                f'<rect x="108" y="20" width="46" height="46" rx="7" fill="{teal}"/>'
                f'<path d="M115 56L124 40L130 48L137 33L147 56" stroke="{paper}" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round"/>'
                f'<circle cx="152" cy="64" r="7" fill="{paper}"/><circle cx="152" cy="64" r="4.5" fill="{sage}" class="blink"/>'
                f'<text x="166" y="33" font-size="11" class="b">Simulating</text>'
                f'<text x="166" y="48" font-size="10.5" class="soft">motor_model.slx</text>'
                f'<rect x="166" y="57" width="120" height="4" rx="2" fill="{t["rule"]}"/>'
                f'<rect x="166" y="57" width="120" height="4" rx="2" fill="{sage}" class="prog"/>')
    return ""


def card(t, repo, idx, total):
    W, H, band = 520, 354, 112
    p = PROJECTS.get(repo["name"], {})
    lang = repo["primaryLanguage"] or {}
    title = p.get("title", repo["name"])
    kind = p.get("kind", lang.get("name") or "Project")
    pitch = p.get("pitch") or clip(repo["description"], 150)
    rel = repo["latestRelease"]
    ci = (((repo.get("defaultBranchRef") or {}).get("target") or {}).get("statusCheckRollup") or {}).get("state")

    o = [f'<clipPath id="cc"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="3.5"/></clipPath>'
         f'<rect x="1" y="1" width="{W - 2}" height="{band - 1}" fill="url(#gp)" clip-path="url(#cc)"/>'
         f'<path d="M1 {band}H{W - 1}" stroke="{t["frame"]}"/>']
    o.append(f'<text x="22" y="32" font-size="11.5" class="mono"><tspan class="teal b">{idx:02d}</tspan><tspan class="soft"> / {total:02d}</tspan></text>')
    label, value = ("RELEASE", rel["tagName"]) if rel else ("STAGE", p.get("stage", "")) if p.get("stage") else ("", "")
    if value:
        o.append(f'<text x="22" y="62" font-size="9.5" class="mono soft" letter-spacing="1.4">{label}</text>'
                 f'<text x="22" y="79" font-size="13" class="mono b">{e(value)}</text>')
    word = ""
    if ci:
        col, word = (t["sage"], "tests passing") if ci == "SUCCESS" else (t["soft"], "tests running") \
            if ci in ("PENDING", "EXPECTED") else (t["teal"], "tests failing")
        o.append(f'<rect x="22" y="92" width="7" height="7" fill="{col}"/>'
                 f'<text x="35" y="99.5" font-size="10.5" class="mono soft">{word}</text>')
    if p.get("art"):
        o.append(f'<g transform="translate(200 12)">{art(t, p["art"])}</g>')

    tsize = 30 if tw(title, 30, serif=True) < 260 else 26
    o.append(f'<text x="22" y="154" font-size="{tsize}" class="serif">{e(title)}</text>')
    if tw(title, tsize, serif=True) + tw(kind, 15, serif=True) + 30 < W - 44:
        o.append(f'<text x="{W - 22}" y="153" font-size="15" class="serif it soft" text-anchor="end">{e(kind)}</text>')
    lines = wrap(pitch, 15.5, W - 44)
    if len(lines) > 3:
        print(f"warning: {repo['name']} pitch wraps to {len(lines)} lines")
    for i, line in enumerate(lines[:3]):
        o.append(f'<text x="22" y="{184 + i * 22}" font-size="15.5" class="body">{e(line)}</text>')

    o.append(f'<path d="M22 248H{W - 22}" stroke="{t["rule"]}"/>')
    for i, (val, cap) in enumerate(p.get("metrics", [])[:2]):
        mx = 22 + i * 252
        o.append(f'<text x="{mx}" y="286" font-size="29" class="serif">{rich(val, 29)}</text>'
                 f'<text x="{mx}" y="306" font-size="12.5" class="soft">{e(cap)}</text>')
        if i == 0:
            o.append(f'<path d="M{mx + 236} 262V308" stroke="{t["rule"]}"/>')

    o.append(f'<path d="M22 320H{W - 22}" stroke="{t["rule"]}"/>')
    meta = f"★ {repo['stargazerCount']} · updated {day(repo['pushedAt'])}"
    o.append(f'<text x="{W - 22}" y="340" font-size="12" class="soft" text-anchor="end">{e(meta)}</text>')
    room = W - 44 - tw(meta, 12) - 16
    parts = (p.get("stack") or lang.get("name") or "").split(" · ")
    while parts and tw(" · ".join(parts), 11.5, mono=True) > room:
        parts.pop()
    o.append(f'<text x="22" y="340" font-size="11.5" class="mono soft">{e(" · ".join(parts))}</text>')

    figures = "; ".join(f"{plain(v)} {c}" for v, c in p.get("metrics", []))
    desc = (f"{title}, {kind.lower()}. {pitch} " + (f"Key numbers: {figures}. " if figures else "")
            + (f"{label.capitalize()}: {value}. " if value else "") + (f"{word.capitalize()}. " if word else "")
            + f"{repo['stargazerCount']} star{'s' if repo['stargazerCount'] != 1 else ''}, updated {day(repo['pushedAt'])}.")
    return svg(t, W, H, title, desc, "\n".join(o), defs=graph_paper(t)), desc


# ---------------------------------------------------------------- stats

def stats(t, d):
    W, H = 1200, 250
    cal = d["weeks"][-26:]
    weekly = [sum(x["contributionCount"] for x in w) for w in cal]
    total = sum(weekly)
    o = [f'<text x="32" y="46" font-size="10" class="mono soft" letter-spacing="1.6">ON GITHUB</text>']
    for i, (v, a, b) in enumerate([(total, "contributions", "last 26 weeks"), (d["repos"], "public repos", "original work"),
                                   (d["stars"], "stars", "across my repos"), (d["followers"], "followers", "and counting")]):
        x, y = 32 + (i % 2) * 150, 102 + (i // 2) * 90
        o.append(f'<text x="{x}" y="{y}" font-size="44" class="serif">{v}</text>'
                 f'<text x="{x}" y="{y + 22}" font-size="13.5" class="body">{a}</text>'
                 f'<text x="{x}" y="{y + 39}" font-size="12" class="soft">{b}</text>')

    x0, x1, base, top = 360, 812, 192, 76
    o.append(f'<path d="M332 30V220M842 30V220" stroke="{t["rule"]}"/>'
             f'<text x="{x0}" y="46" font-size="10" class="mono soft" letter-spacing="1.6">WEEKLY CONTRIBUTIONS · 26 WEEKS</text>'
             f'<path d="M{x0} {base}H{x1}" stroke="{t["frame"]}"/>')
    slot, peak = (x1 - x0) / len(weekly), max(weekly) or 1
    best, labelled = weekly.index(peak), -9
    for i, v in enumerate(weekly):
        h = (base - top) * v / peak
        x = x0 + i * slot + (slot - 9) / 2
        if v:
            o.append(f'<rect x="{x:.1f}" y="{base - h:.1f}" width="9" height="{h:.1f}" fill="{t["teal"] if i == best else t["ink"]}" '
                     f'fill-opacity="{1 if i == best else .82}" class="bar" style="animation-delay:{i * .025:.3f}s"/>')
        else:
            o.append(f'<rect x="{x:.1f}" y="{base - 1.5}" width="9" height="1.5" fill="{t["faint"]}"/>')
        first = dt.date.fromisoformat(cal[i][0]["date"])
        new_month = i == 0 or first.month != dt.date.fromisoformat(cal[i - 1][0]["date"]).month
        if new_month and i - labelled >= 3 and i < len(weekly) - 2:
            o.append(f'<text x="{x:.1f}" y="{base + 18}" font-size="10" class="mono soft">{first.strftime("%b")}</text>')
            labelled = i
    bx = x0 + best * slot + slot / 2
    o.append(f'<text x="{bx:.1f}" y="{base - (base - top) - 8}" font-size="10" class="mono teal" text-anchor="middle">{peak}</text>')

    rx, rw = 872, 296
    o.append(f'<text x="{rx}" y="46" font-size="10" class="mono soft" letter-spacing="1.6">LANGUAGES · 12 MONTHS</text>')
    top5 = d["langs"][:5]
    tot = sum(s for _, s in top5) or 1
    for i, (name, size) in enumerate(top5):
        y = 82 + i * 30
        share = size / tot
        o.append(f'<text x="{rx}" y="{y}" font-size="14.5">{e(name)}</text>'
                 f'<text x="{rx + rw}" y="{y}" font-size="12" class="mono soft" text-anchor="end">{100 * share:.1f}%</text>'
                 f'<rect x="{rx}" y="{y + 7}" width="{rw}" height="2" fill="{t["rule"]}"/>'
                 f'<rect x="{rx}" y="{y + 7}" width="{rw * share / (top5[0][1] / tot):.1f}" height="2" '
                 f'fill="{t["teal"] if i == 0 else t["ink"]}" class="grow" style="animation-delay:{i * .1:.1f}s"/>')

    desc = (f"GitHub activity: {total} contributions in the last 26 weeks, {d['repos']} public repositories, {d['stars']} stars, "
            f"{d['followers']} followers. Busiest week: {peak}. Languages over the last 12 months: "
            + ", ".join(f"{n} {100 * s / tot:.0f}%" for n, s in top5) + ".")
    return svg(t, W, H, "GitHub activity", desc, "\n".join(o))


# ---------------------------------------------------------------- static pieces

def kpis(t):
    W, H = 1200, 200
    tiles = [("10^{−13}", " pu", "match with the PYPOWER reference", "swingbus"),
             ("8.3", " ms", "full N-1 screen of a 118-bus grid", "swingbus"),
             ("2.4", "×", "faster maze runs with clothoid turns", "ariadne"),
             ("99.6", "%", "top-1 gesture recognition on-device", "malfoid"),
             ("230", "+", "automated tests in CI across 4 repos", "4 repos")]
    cw = W / len(tiles)
    o = []
    for i, (num, unit, label, src) in enumerate(tiles):
        x = i * cw + 30
        if i:
            o.append(f'<path d="M{i * cw:.0f} 30V170" stroke="{t["rule"]}"/>')
        o.append(f'<text x="{x:.0f}" y="50" font-size="15" class="serif it soft"><tspan class="mono teal b" font-style="normal" font-size="11">{i + 1:02d}</tspan>  {e(src)}</text>'
                 f'<text x="{x:.0f}" y="114" font-size="52" class="serif" letter-spacing="-1">{rich(num, 52)}'
                 f'<tspan font-size="26" class="it teal">{e(unit)}</tspan></text>')
        lines = wrap(label, 14.5, cw - 60)
        if len(lines) > 2:
            print(f"warning: kpi label wraps to {len(lines)} lines: {label}")
        for j, line in enumerate(lines[:2]):
            o.append(f'<text x="{x:.0f}" y="{146 + j * 20}" font-size="14.5" class="body">{e(line)}</text>')
    desc = "Proof in numbers: " + "; ".join(f"{plain(n)}{u} {l} ({s})" for n, u, l, s in tiles) + "."
    return svg(t, W, H, "Proof in numbers", desc, "\n".join(o))


def section(t, num, title, note):
    W, H = 1200, 64
    tx = 24 + tw(num, 12, mono=True) + 18
    end = tx + tw(title, 32, serif=True) + 22
    nx = W - 24 - tw(note, 15, serif=True)
    # opaque, so it stays readable even if GitHub's theme and the system theme disagree
    o = [f'<rect width="{W}" height="{H}" rx="4" fill="{t["paper"]}"/>',
         f'<text x="24" y="42" font-size="12" class="mono teal b">{num}</text>',
         f'<text x="{tx:.0f}" y="44" font-size="32" class="serif" letter-spacing="-.4">{e(title)}</text>',
         f'<path d="M{end:.0f} 36H{nx - 20:.0f}" stroke="{t["frame"]}"/>',
         f'<text x="{W - 24}" y="41" font-size="15" class="serif it soft" text-anchor="end">{e(note)}</text>']
    return svg(t, W, H, f"{num} {title}", f"{num}. {title}. {note}.", "\n".join(o), card=False)


def skills(t):
    W = 1200
    cols = [("A", "GRIDS & ENERGY", ["Power flow (Newton-Raphson)", "Three-phase", "P/Q/S", "Power factor", "Transformers",
                                    "N-1 contingency", "DC-OPF and LMPs", "Synchrophasors", "IEEE C37.118", "MATPOWER cases"]),
            ("B", "EMBEDDED & MEASUREMENT", ["ESP32 and ESP32-S3", "C and C++", "ESP-IDF", "FreeRTOS", "PlatformIO", "KiCad",
                                            "MQTT", "Oscilloscope", "IMUs and sensors", "Arduino"]),
            ("C", "SOFTWARE & TOOLS", ["Python", "MATLAB", "Simulink", "NumPy", "SciPy", "PyTorch", "XGBoost", "SHAP",
                                      "pytest", "Docker", "GitHub Actions", "Git", "Linux", "LaTeX"])]
    cw, fs, lead = W / 3, 15.5, 27
    o, height = [], 0
    for i, (letter, title, items) in enumerate(cols):
        x0 = i * cw + 32
        o.append(f'<text x="{x0:.0f}" y="48" font-size="10" class="mono" letter-spacing="1.6"><tspan class="teal b">{letter}</tspan>'
                 f'<tspan class="soft">  {e(title)}</tspan></text>')
        lines, cur, width = [], [], cw - 64
        for item in items:
            trial = cur + [item]
            if cur and tw(" / ".join(trial), fs) > width:
                lines.append(cur)
                cur = [item]
            else:
                cur = trial
        lines.append(cur)
        for j, line in enumerate(lines):
            spans = '<tspan class="faint">  /  </tspan>'.join(f"<tspan>{e(it)}</tspan>" for it in line)
            o.append(f'<text x="{x0:.0f}" y="{84 + j * lead}" font-size="{fs}">{spans}</text>')
        height = max(height, 84 + (len(lines) - 1) * lead + 34)
        if i:
            o.append(f'<path d="M{i * cw:.0f} 28V{{H}}" stroke="{t["rule"]}"/>')

    # certifications under the first two columns, languages under the third
    certs = [("Electric Power Systems", "University at Buffalo, Coursera"),
             ("Mobilités et véhicules électriques", "École des Ponts ParisTech, Coursera"),
             ("MATLAB, Simulink and Simscape Onramp", "MathWorks")]
    langs = [("Arabic", "native", 5), ("French", "fluent", 4), ("English", "professional", 4)]
    top, step = height + 2, 30
    lx = 2 * cw + 32
    o.append(f'<path d="M32 {top}H{W - 32}" stroke="{t["rule"]}"/>'
             f'<path d="M{2 * cw:.0f} {top + 22}V{top + 64 + len(certs) * step}" stroke="{t["rule"]}"/>')
    for x, letter, title in ((32, "D", "CERTIFICATIONS"), (lx, "E", "LANGUAGES")):
        o.append(f'<text x="{x:.0f}" y="{top + 40}" font-size="10" class="mono" letter-spacing="1.6"><tspan class="teal b">{letter}</tspan>'
                 f'<tspan class="soft">  {title}</tspan></text>')
    for i, (name, issuer) in enumerate(certs):
        y = top + 76 + i * step
        o.append(f'<rect x="32" y="{y - 12}" width="14" height="14" rx="2" fill="{t["teal"]}"/>'
                 f'<path d="M35.4 {y - 5}L38.2 {y - 2.3}L42.8 {y - 8}" stroke="{t["paper"]}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>'
                 f'<text x="58" y="{y}" font-size="{fs}">{e(name)}<tspan class="soft" font-size="13">  ·  {e(issuer)}</tspan></text>')
    for i, (lang, level, n) in enumerate(langs):
        y = top + 76 + i * step
        o.append(f'<text x="{lx:.0f}" y="{y}" font-size="{fs}">{e(lang)}<tspan class="soft" font-size="13">  ·  {e(level)}</tspan></text>')
        for k in range(5):
            o.append(f'<rect x="{W - 32 - (5 - k) * 30 + 4}" y="{y - 8}" width="26" height="5" rx="2.5" '
                     f'fill="{t["teal"] if k < n else t["rule"]}" class="grow" style="animation-delay:{.08 * k + .12 * i:.2f}s"/>')
    H = top + 76 + (len(certs) - 1) * step + 34
    body = "\n".join(o).replace("{H}", str(top - 14))
    desc = ("Toolkit. " + " ".join(f"{title.capitalize()}: {', '.join(items)}." for _, title, items in cols)
            + " Certifications: " + "; ".join(f"{c}, {i}" for c, i in certs) + ". Languages: "
            + ", ".join(f"{lang} ({level})" for lang, level, _ in langs) + ".")
    return svg(t, W, H, "Toolkit, certifications and languages", desc, body)


def button(t, label, mark, primary=False):
    W, H = 224, 52
    if primary:
        body = (f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="3" fill="{t["teal"]}"/>'
                f'<text x="{W / 2}" y="32.5" font-size="17" class="b" text-anchor="middle" style="fill:{t["paper"]}">{e(label)}  {mark}</text>')
    else:
        body = (f'<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="3" fill="{t["paper"]}" stroke="{t["ink"]}" stroke-opacity=".55" stroke-width="1.2"/>'
                f'<text x="{W / 2}" y="32.5" font-size="17" class="b" text-anchor="middle">{e(label)}  <tspan class="teal">{mark}</tspan></text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none" role="img" '
            f'aria-label="{e(label)}"><title>{e(label)}</title><defs><style>{css(t)}</style></defs>{body}</svg>\n')


def contact(t):
    W, H = 1200, 320
    rows = [("WHEN", "Summer 2027", "1 to 2 months, dates on request"),
            ("WHERE", "Morocco or abroad", "on-site, hybrid or remote"),
            ("FIELDS", "Power and energy systems", "studies, operations, maintenance, automation"),
            ("EMAIL", EMAIL, f"or {LINKEDIN}"),
            ("WEB", SITE, "portfolio")]
    step = (H - 64) / len(rows)
    o = [f'<text x="48" y="62" font-size="16" class="serif it soft"><tspan class="mono teal b" font-style="normal" font-size="12">04</tspan>  Let us talk</text>',
         f'<text x="46" y="134" font-size="46" class="serif" letter-spacing="-.8">Hiring a first-year</text>',
         f'<text x="46" y="186" font-size="46" class="serif" letter-spacing="-.8">engineering intern?</text>',
         f'<text x="48" y="224" font-size="17" class="body">Stage d\'initiation. My CV has it all on one page, in French.</text>',
         f'<rect x="48" y="246" width="232" height="46" rx="3" fill="{t["teal"]}"/>'
         f'<text x="164" y="275" font-size="16.5" class="b" text-anchor="middle" style="fill:{t["paper"]}">Download my CV  ↓</text>',
         f'<path d="M620 32V{H - 32}" stroke="{t["rule"]}"/>']
    for i, (k, v, s) in enumerate(rows):
        y = 32 + i * step
        o.append(f'<text x="652" y="{y + 27:.0f}" font-size="10" class="mono soft" letter-spacing="1.6">{k}</text>'
                 f'<text x="782" y="{y + 23:.0f}" font-size="15.5" class="b">{e(v)}</text>'
                 f'<text x="782" y="{y + 41:.0f}" font-size="13" class="soft">{e(s)}</text>')
        if i < len(rows) - 1:
            o.append(f'<path d="M652 {y + step:.0f}H1160" stroke="{t["rule"]}"/>')
    desc = ("Hiring a first-year engineering intern? Stage d'initiation. My CV has it all on one page, in French. "
            + " ".join(f"{k.capitalize()}: {v}, {s}." for k, v, s in rows) + " Click to download my CV.")
    return svg(t, W, H, "Contact", desc, "\n".join(o))


# ---------------------------------------------------------------- off GitHub: the bench, and my background

def tipe(t):
    """The one project that lives on a bench, not on GitHub: resonant wireless power transfer (TIPE, CPGE)."""
    W, H, P = 1200, 320, 470
    ink, teal, sage, soft, frame, paper = t["ink"], t["teal"], t["sage"], t["soft"], t["frame"], t["paper"]
    o = [f'<clipPath id="tc"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="3.5"/></clipPath>'
         f'<rect x="1" y="1" width="{P}" height="{H - 2}" fill="url(#gp)" clip-path="url(#tc)"/>'
         f'<path d="M{P} 1V{H - 1}" stroke="{frame}"/>']

    # Fig. 2a: source, series capacitor and transmit coil; receive coil, capacitor and load
    cy, ry = 92, 36
    tx, rx = [104 + 8 * k for k in range(6)], [306 + 8 * k for k in range(6)]
    for xs in (tx, rx):
        o += [f'<ellipse cx="{x}" cy="{cy}" rx="6" ry="{ry}" stroke="{ink}" stroke-width="1.3"/>' for x in xs]
    # mutual flux: along the shared axis, and bowing across the gap
    flux = [f"M{tx[0] - 10} {cy}H{rx[-1] + 10}"] + [
        f"M{tx[-1]} {cy + s * 18}C{tx[-1] + 44} {cy + s * 52} {rx[0] - 44} {cy + s * 52} {rx[0]} {cy + s * 18}" for s in (-1, 1)]
    o += [f'<path d="{p}" stroke="{teal}" stroke-width="1.5" class="flow" style="animation-duration:{1.1 + k * .2:.1f}s"/>'
          for k, p in enumerate(flux)]
    top, bot = cy - ry, cy + ry
    o.append(f'<path d="M{tx[0]} {top}H86M80 {top}H58V{cy - 12}M58 {cy + 12}V{bot}H{tx[0]}" stroke="{ink}" stroke-width="1.3"/>'
             f'<circle cx="58" cy="{cy}" r="12" stroke="{ink}" stroke-width="1.3" fill="{paper}"/>'
             f'<path d="M51 {cy}q3.5 -6 7 0t7 0" stroke="{ink}" stroke-width="1.3"/>'
             f'<path d="M80 {top - 8}V{top + 8}M86 {top - 8}V{top + 8}" stroke="{ink}" stroke-width="1.6"/>'
             f'<path d="M{rx[-1]} {top}H378M384 {top}H418V{cy - 16}l6 3l-12 5l12 5l-12 5l6 3V{bot}H{rx[-1]}" stroke="{ink}" stroke-width="1.3" stroke-linejoin="round"/>'
             f'<path d="M378 {top - 8}V{top + 8}M384 {top - 8}V{top + 8}" stroke="{ink}" stroke-width="1.6"/>')
    o.append(f'<text x="{tx[2] + 4}" y="{bot + 22}" font-size="10" class="mono soft" text-anchor="middle">TX</text>'
             f'<text x="{rx[2] + 4}" y="{bot + 22}" font-size="10" class="mono soft" text-anchor="middle">RX</text>'
             f'<text x="58" y="{top - 14}" font-size="10" class="mono soft" text-anchor="middle">GBF</text>'
             f'<text x="430" y="{cy + 4}" font-size="10" class="mono soft">R</text>')
    # dimension line for the 14 cm gap, as on a drawing
    dy_ = bot + 32
    o.append(f'<path d="M{tx[-1] + 6} {bot + 8}V{dy_ + 6}M{rx[0] - 6} {bot + 8}V{dy_ + 6}M{tx[-1] + 6} {dy_}H{rx[0] - 6}" stroke="{soft}"/>'
             f'<path d="M{tx[-1] + 6} {dy_}l7 -3v6zM{rx[0] - 6} {dy_}l-7 -3v6z" fill="{soft}"/>'
             f'<text x="{(tx[-1] + rx[0]) / 2:.0f}" y="{dy_ - 6}" font-size="10" class="mono soft" text-anchor="middle">d = 14 cm</text>')

    # Fig. 2b: series RLC current response with the measured Q, peaking at the 34 kHz tuning
    gx0, gx1, base, peak = 44, 430, 286, 196
    f0, Q, f_lo, f_hi = 34.0, 16.9, 26.0, 42.0
    def gx(f):
        return gx0 + (gx1 - gx0) * (f - f_lo) / (f_hi - f_lo)
    pts = []
    for i in range(0, 321):
        f = f_lo + (f_hi - f_lo) * i / 320
        amp = 1 / math.sqrt(1 + Q * Q * (f / f0 - f0 / f) ** 2)
        pts.append(f"{gx(f):.1f},{base - (base - peak) * amp:.1f}")
    o.append(f'<path d="M{gx0} {base}H{gx1}M{gx0} {base}V{peak - 12}" stroke="{frame}"/>'
             f'<path d="M{gx(f0):.1f} {peak - 4}V{base}" stroke="{soft}" stroke-dasharray="2 4"/>'
             f'<style>.sweep{{stroke-dasharray:900;animation:sweep 6s cubic-bezier(.45,0,.2,1) infinite}}'
             f'@keyframes sweep{{0%{{stroke-dashoffset:900}}55%,88%{{stroke-dashoffset:0;opacity:1}}100%{{stroke-dashoffset:0;opacity:0}}}}</style>'
             f'<polyline points="{" ".join(pts)}" stroke="{sage}" stroke-width="1.8" class="sweep"/>'
             f'<text x="{gx(37):.0f}" y="{peak + 6}" font-size="10" class="mono teal">f0 = 34 kHz</text>'
             f'<text x="{gx(37):.0f}" y="{peak + 20}" font-size="10" class="mono soft">Q ≈ 16.9</text>'
             f'<text x="{gx0 + 6}" y="{peak - 2}" font-size="10" class="mono soft">|i|</text>'
             f'<text x="{gx1}" y="{base + 16}" font-size="9" class="mono faint" text-anchor="end">f, kHz</text>')
    for f in (30, 38):
        o.append(f'<path d="M{gx(f):.1f} {base}V{base + 4}" stroke="{frame}"/>'
                 f'<text x="{gx(f):.1f}" y="{base + 16}" font-size="9" class="mono faint" text-anchor="middle">{f}</text>')

    # the write-up
    x0, x1 = P + 34, W - 32
    o.append(f'<text x="{x0}" y="46" font-size="11" class="mono" letter-spacing="1.4"><tspan class="teal b">OFF GITHUB</tspan>'
             f'<tspan class="soft">  ·  TIPE, CPGE RESEARCH PROJECT  ·  PHYSICAL BENCH</tspan></text>'
             f'<text x="{x0}" y="88" font-size="30" class="serif">Wireless power transfer</text>'
             f'<text x="{x1}" y="87" font-size="15" class="serif it soft" text-anchor="end">Resonant inductive coupling</text>')
    pitch = ("Two coupled coils, first as a plain RL link, then as RLC circuits tuned to resonance. At 14 cm "
             "the tuned link still delivers 13%, against 0.3% untuned. Next step: Litz wire.")
    lines = wrap(pitch, 15.5, x1 - x0)
    for i, line in enumerate(lines[:3]):
        o.append(f'<text x="{x0}" y="{122 + i * 22}" font-size="15.5" class="body">{e(line)}</text>')
    o.append(f'<path d="M{x0} 196H{x1}" stroke="{t["rule"]}"/>')
    metrics = [("23%", "efficiency, up from 7.4%"), ("R^{2} = 0.992", "model against the bench"), ("Q ≈ 16.9", "quality factor, k = 0.044")]
    mw = (x1 - x0) / 3
    for i, (val, cap) in enumerate(metrics):
        mx = x0 + i * mw
        o.append(f'<text x="{mx:.0f}" y="238" font-size="29" class="serif">{rich(val, 29)}</text>'
                 f'<text x="{mx:.0f}" y="258" font-size="12.5" class="soft">{e(cap)}</text>')
        if i:
            o.append(f'<path d="M{mx - 18:.0f} 212V260" stroke="{t["rule"]}"/>')
    o.append(f'<path d="M{x0} 276H{x1}" stroke="{t["rule"]}"/>'
             f'<text x="{x0}" y="298" font-size="11.5" class="mono soft">RLC coupling · signal generator · oscilloscope · Python</text>'
             f'<text x="{x1}" y="298" font-size="12" class="soft" text-anchor="end">Fig. 2. Bench and current response</text>')

    desc = (f"Wireless power transfer, TIPE research project in CPGE, on a physical bench. {pitch} "
            "Key numbers: 23% efficiency at 34 kHz, up from 7.4% on the RL bench; model validated with R squared 0.992; "
            "coupling k = 0.044; quality factor Q about 16.9. Tools: RLC coupling, signal generator, oscilloscope, Python. "
            "Figure: transmit and receive coils 14 cm apart with their capacitors, and the resonance curve at 34 kHz.")
    return svg(t, W, H, "Wireless power transfer, TIPE", desc, "\n".join(o), defs=graph_paper(t))


def background(t):
    """School and clubs as a one-line diagram: each school a station on the line, each club role a feeder off it."""
    W, H, y = 1200, 356, 168
    ink, teal, sage, paper = t["ink"], t["teal"], t["sage"], t["paper"]
    now = 2
    stations = [(56, "2024", "Sefrou", "Baccalauréat", "Sciences Maths B", "Mention Très Bien, Lycée Le Jasmin 2"),
                (361, "2024 to 2026", "Meknès", "CPGE, MP track", "Lycée Omar Ibn Al Khattab", "then admitted to EHTP via the CNC"),
                (680, "2026 to 2029", "Casablanca", "EHTP, Ingénieur d'État", "Electrical and Energy Engineering", "now in year 1 of 3"),
                (980, "Next", "summer 2027", "Your team?", "this slot is open", "")]
    feeders = [(400, "Sept 2024 to June 2026", "Vice-president & trainer", "BeurdByte Builders club, CPGE",
                "Trained students in C, Arduino, ESP and IoT, and coached them to a working prototype."),
               (680, "Since Oct 2026", "Visits & Workshops unit", "Club Electro-Power, EHTP",
                "Member, organizing industrial visits and microcontroller workshops.")]
    notes = [("CPGE", "two-year prep for the engineering schools"), ("CNC", "national entrance exam to those schools"),
             ("EHTP", "École Hassania des Travaux Publics"), ("Bac", "Mention Très Bien is the top honours band")]

    # the line: live up to the school I am at, dashed after it
    o = []
    for a, b in ((73, 339), (383, 680)):
        o.append(f'<path d="M{a} {y}H{b}" stroke="{ink}" stroke-width="1.4"/>'
                 f'<path d="M{a} {y}H{b}" stroke="{teal}" stroke-width="1.6" class="flow"/>')
    o.append(f'<path d="M680 {y}H973M987 {y}H1148" stroke="{sage}" stroke-width="1.4" stroke-dasharray="5 6"/>'
             f'<path d="M1148 {y - 6}L1160 {y}L1148 {y + 6}Z" fill="{sage}"/>')
    # generator, transformer, busbar, open breaker
    o.append(f'<circle cx="56" cy="{y}" r="17" stroke="{ink}" stroke-width="1.4" fill="{paper}"/>'
             f'<path d="M47 {y}q4.5 -8 9 0t9 0" stroke="{ink}" stroke-width="1.4"/>'
             f'<circle cx="352" cy="{y}" r="13" stroke="{ink}" stroke-width="1.4"/>'
             f'<circle cx="370" cy="{y}" r="13" stroke="{ink}" stroke-width="1.4"/>'
             f'<path d="M680 {y - 26}V{y + 26}" stroke="{teal}" stroke-width="5"/>'
             f'<circle cx="680" cy="{y}" r="5" stroke="{teal}" class="ring"/>'
             f'<rect x="973" y="{y - 7}" width="14" height="14" fill="{paper}" stroke="{sage}" stroke-width="1.4"/>')
    for i, (sx, when, where, title, sub, detail) in enumerate(stations):
        x = sx - 16
        o.append(f'<text x="{x}" y="56" font-size="10.5" class="mono" letter-spacing="1.4"><tspan class="{"sage" if i > now else "teal"} b">'
                 f'{e(when.upper())}</tspan><tspan class="soft">  ·  {e(where.upper())}</tspan></text>'
                 f'<text x="{x}" y="86" font-size="21" class="serif">{e(title)}</text>'
                 f'<text x="{x}" y="108" font-size="14.5" class="{"soft it serif" if i > now else "body"}">{e(sub)}</text>')
        if detail:
            o.append(f'<text x="{x}" y="128" font-size="13" class="{"teal" if i == now else "soft"}">{e(detail)}</text>')

    for fx, when, role, org, line in feeders:
        o.append(f'<path d="M{fx} {y + (26 if fx == 680 else 0)}V{H - 34}" stroke="{ink}" stroke-width="1.3"/>'
                 f'<path d="M{fx - 6} {H - 36}L{fx} {H - 25}L{fx + 6} {H - 36}Z" fill="{ink}"/>')
        if fx != 680:
            o.append(f'<circle cx="{fx}" cy="{y}" r="3.5" fill="{ink}"/>')
        x = fx + 20
        o.append(f'<text x="{x}" y="216" font-size="10.5" class="mono" letter-spacing="1.4"><tspan class="teal b">{e(when.upper())}</tspan></text>'
                 f'<text x="{x}" y="242" font-size="18" class="serif">{e(role)}</text>'
                 f'<text x="{x}" y="263" font-size="14.5" class="serif it teal">{e(org)}</text>')
        for j, part in enumerate(wrap(line, 13, 240)[:3]):
            o.append(f'<text x="{x}" y="{288 + j * 19}" font-size="13" class="soft">{e(part)}</text>')

    # notes for readers who do not know the Moroccan system, and a legend, as on any drawing
    o.append(f'<text x="40" y="216" font-size="10" class="mono soft" letter-spacing="1.6">NOTES</text>')
    for j, (k, v) in enumerate(notes):
        o.append(f'<text x="40" y="{242 + j * 22}" font-size="10.5" class="mono teal b">{k}</text>'
                 f'<text x="86" y="{242 + j * 22}" font-size="12.5" class="soft">{e(v)}</text>')
    o.append(f'<text x="980" y="216" font-size="10" class="mono soft" letter-spacing="1.6">LEGEND</text>')
    keys = [(f'<path d="M980 238H1006" stroke="{ink}" stroke-width="1.4"/><path d="M980 238H1006" stroke="{teal}" stroke-width="1.6" class="flow"/>', "done"),
            (f'<path d="M993 251V269" stroke="{teal}" stroke-width="5"/>', "where I am now"),
            (f'<path d="M980 282H1006" stroke="{sage}" stroke-width="1.4" stroke-dasharray="5 6"/>', "next"),
            (f'<path d="M993 294V304" stroke="{ink}" stroke-width="1.3"/><path d="M988 302L993 310L998 302Z" fill="{ink}"/>', "role held alongside")]
    for j, (mark, label) in enumerate(keys):
        o.append(f'{mark}<text x="1018" y="{242 + j * 22}" font-size="12.5" class="soft">{label}</text>')

    desc = ("Background, drawn as a one-line diagram. "
            + " ".join(f"{w}, {p}: {ti}, {su}{', ' + d if d else ''}." for _, w, p, ti, su, d in stations)
            + " Roles held alongside: " + " ".join(f"{w}: {r}, {g}. {line}" for _, w, r, g, line in feeders)
            + " Notes: " + "; ".join(f"{k}: {v}" for k, v in notes) + ".")
    return svg(t, W, H, "Background", desc, "\n".join(o))


# ---------------------------------------------------------------- README pinned block

def themed(name, alt, width):
    return f'<img src="./assets/{name}.svg" width="{width}" alt="{e(alt)}">'


def readme_block(alts, pins):
    rows = []
    for i in range(0, len(pins), 2):
        cells = [f'  <a href="https://github.com/{USER}/{p["name"]}">{themed(f"pin-{i + j + 1}", alts[i + j], "49%")}</a>'
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

    emit("header", header, d)
    emit("stats", stats, d)
    alts, n = [], len(d["pins"])
    for i, repo in enumerate(d["pins"], 1):
        content, alt = card(LOGO, repo, i, n)
        write(f"pin-{i}.svg", content)
        alts.append(alt)
    for i in range(n + 1, 7):
        path = os.path.join(ASSETS, f"pin-{i}.svg")
        if os.path.exists(path):
            os.remove(path)
            print(f"removed assets/pin-{i}.svg")
    update_readme(readme_block(alts, d["pins"]))

    emit("kpis", kpis)
    emit("tipe", tipe)
    emit("background", background)
    emit("skills", skills)
    emit("section-work", section, "01", "Selected work", "Synced with my GitHub pins")
    emit("section-background", section, "02", "Background", "School and clubs, as a one-line diagram")
    emit("section-toolkit", section, "03", "Toolkit and activity", "What I work with")
    emit("contact", contact)
    emit("btn-cv", button, "Download CV", "↓", True)
    emit("btn-email", button, "Email me", "↗")
    emit("btn-site", button, SITE, "↗")
    emit("btn-linkedin", button, "LinkedIn", "↗")
    emit("btn-work", button, "See projects", "↓")


if __name__ == "__main__":
    main()
