#!/usr/bin/env python3
"""Draw the profile's widgets into assets/ and rewrite README.md's marked blocks.

Inputs: hrabovskyi.online/status.json (written by cron on the box every
10 minutes), hrabovskyi.online/feed.json (the site's build) and the GitHub API
(repo languages). Stack icons are vendored from skillicons.dev (MIT) into
assets/icons, since they never change. A widget is redrawn only
when its inputs arrived; otherwise the last drawing stays and the problem is
reported through GITHUB_OUTPUT so the run goes red.

A status older than the site's own cut-off is drawn as silent, never as the
last good numbers. Stdlib only, so the Action needs no install step.
"""
import base64, html, http.client, json, os, re, sys, time, urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
README = os.path.join(ROOT, "README.md")
SITE = "https://hrabovskyi.online"
MAX_AGE_HOURS = 48  # same cut-off as the site's lib/status.ts

# The site's tokens (personal-website app/globals.css), so the profile and the site read as one thing.
THEMES = {
    "dark": dict(card="#111215", tile="#16181b", border="#23262b", fg="#f2f4f6", muted="#98a0a8",
                 faint="#5b616a", brand="#f2a03d", ok="#4ade80", info="#60a5fa", violet="#a78bfa", bad="#f87171"),
    "light": dict(card="#ffffff", tile="#f5f6f7", border="#e4e6ea", fg="#0d0e10", muted="#5b6169",
                  faint="#9aa0a8", brand="#a85d08", ok="#15803d", info="#1d4ed8", violet="#6d28d9", bad="#b91c1c"),
}
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, 'SF Mono', Menlo, 'Cascadia Mono', 'DejaVu Sans Mono', monospace"

LANGUAGE_COLORS = {"C#": "#3fb950", "Python": "#4b8bd4", "Kotlin": "#a97bff", "JavaScript": "#f1e05a",
                   "TypeScript": "#3178c6", "TSX": "#3178c6", "Markdown": "#8b949e", "Html": "#e34c26",
                   "HTML": "#e34c26", "Bash": "#89e051", "Shell": "#89e051", "YAML": "#cb171e", "Json": "#c9a26b"}

PROJECTS = [
    # repo, title, status, tagline (pre-wrapped: SVG text does not wrap), tags
    ("Egoushka/attest", "Attest", "on nuget",
     ["National ID, tax ID, VAT and postal codes", "for 87 countries, each by its own rule."], "netstandard · NuGet"),
    ("Egoushka/chargehand", "chargehand", "running",
     ["Runs a codebase question on coding agents,", "checks every citation against a commit."], "CLI · HTTP · MCP"),
    ("Egoushka/chronicle", "Chronicle", "running",
     ["Seven years of my chat history, searchable", "by an assistant over MCP."], "pgvector · MCP"),
    ("nytka-app/server", "Nytka", "building",
     ["A self-hosted home for an Omi necklace's", "conversations, memories and action items."], "ASP.NET Core · Android"),
    ("Egoushka/switchboard", "switchboard", "running",
     ["One MCP front door to every tool", "on the homelab."], "MCP gateway"),
    ("Egoushka/devbox-mcp", "devbox-mcp", "running",
     ["A project's real test suite and SonarQube", "scan, in throwaway containers."], "MCP · Docker"),
]
STATUS_COLOR = {"on nuget": "brand", "running": "ok", "building": "info"}

STACK = [
    ("day job", ["cs", "dotnet", "angular", "ts"]),
    ("own projects", ["py", "kotlin", "postgres", "nextjs"]),
    ("the box", ["docker", "linux", "cloudflare", "redis", "grafana", "prometheus", "githubactions", "bash"]),
]
ICON_NAMES = {"cs": "C#", "dotnet": ".NET", "angular": "Angular", "ts": "TypeScript", "py": "Python",
              "kotlin": "Kotlin", "postgres": "Postgres", "nextjs": "Next.js", "docker": "Docker", "linux": "Linux",
              "cloudflare": "Cloudflare", "redis": "Redis", "grafana": "Grafana", "prometheus": "Prometheus",
              "githubactions": "Actions", "bash": "Bash"}

REPO_ICON = ("M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 "
             "0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 "
             "9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087a.249.249 0 0 0-.3 "
             "0L5.4 15.7a.25.25 0 0 1-.4-.2Z")

problems = []


def esc(s):
    return html.escape(str(s), quote=True)


def fetch(url, raw=False):
    headers = {"User-Agent": "Egoushka/Egoushka profile renderer"}
    if url.startswith("https://api.github.com/") and os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    for attempt_no in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=20) as r:
                body = r.read()
            return body if raw else json.loads(body)
        except (OSError, http.client.IncompleteRead, json.JSONDecodeError):
            if attempt_no == 2:
                raise
            time.sleep(2 * (attempt_no + 1))


def attempt(what, fn):
    try:
        return fn()
    except Exception as e:  # any failure keeps the last drawing; the run reports it
        problems.append(f"{what}: {type(e).__name__}: {e}")
        return None


def svg(w, h, t, label, body, css="", defs="", backdrop="", below=0):
    """A card of w by h; `below` adds transparent space under it, since stacked images on GitHub touch."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h + below}" viewBox="0 0 {w} {h + below}" role="img" aria-label="{esc(label)}">
<style>
text {{ font-family: {SANS}; }}
.mono {{ font-family: {MONO}; }}
.rise {{ animation: rise .7s cubic-bezier(.2,.7,.2,1) both; }}
@keyframes rise {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: none; }} }}
{css}
@media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
</style>
<defs><clipPath id="frame"><rect width="{w}" height="{h}" rx="16"/></clipPath>{defs}</defs>
<g clip-path="url(#frame)"><rect width="{w}" height="{h}" fill="{t['card']}"/>{backdrop}</g>
{body}
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="15.5" fill="none" stroke="{t['border']}"/>
</svg>
"""


def edge(t, w, h):
    """The site's accent, as a 3px gradient along the bottom edge."""
    return (f'<linearGradient id="edge" x1="0" x2="1"><stop offset="0" stop-color="{t["brand"]}"/>'
            f'<stop offset=".55" stop-color="{t["violet"]}"/><stop offset="1" stop-color="{t["info"]}"/></linearGradient>',
            f'<rect y="{h - 3}" width="{w}" height="3" fill="url(#edge)"/>')


def title(t, x, y, text, color=None):
    return (f'<text class="mono" x="{x}" y="{y}" font-size="14" letter-spacing="2.5" '
            f'fill="{t[color or "brand"]}">{esc(text.upper())}</text>')


# ---------------------------------------------------------------- header

def typing(t, phrases, x, y, size):
    """A typewriter in SMIL: one clip per phrase, all driven by one shared timeline."""
    cw, step, erase, hold, gap = size * 0.6, 0.055, 0.022, 2.4, 0.45
    events, now = [], 0.0
    for i, p in enumerate(phrases):
        for k in range(len(p) + 1):
            events.append((now + k * step, i, k))
        now += len(p) * step + hold
        for k in range(len(p) - 1, -1, -1):
            now += erase
            events.append((now, i, k))
        now += gap
    events.append((now, len(phrases) - 1, 0))
    times = ";".join(f"{e[0] / now:.5f}" for e in events)
    anim = f'dur="{now:.2f}s" repeatCount="indefinite" calcMode="discrete" keyTimes="{times}"'
    out = []
    for i, p in enumerate(phrases):
        widths = ";".join(f"{k * cw if j == i else 0:.1f}" for _, j, k in events)
        out.append(f'<clipPath id="type{i}"><rect x="{x}" y="{y - size}" height="{size * 1.5}" width="0">'
                   f'<animate attributeName="width" {anim} values="{widths}"/></rect></clipPath>'
                   f'<text class="mono" x="{x}" y="{y}" font-size="{size}" fill="{t["brand"]}" '
                   f'textLength="{len(p) * cw:.1f}" lengthAdjust="spacing" clip-path="url(#type{i})">{esc(p)}</text>')
    xs = ";".join(f"{x + k * cw + 3:.1f}" for _, _, k in events)
    out.append(f'<rect class="cursor" x="{x}" y="{y - size * 0.82:.1f}" width="{size * 0.5:.1f}" height="{size * 1.02:.1f}" '
               f'rx="2" fill="{t["brand"]}"><animate attributeName="x" {anim} values="{xs}"/></rect>')
    return "".join(out)


def rack(t, x, y, live, caption):
    units, out = 5, []
    out.append(f'<rect x="{x}" y="{y}" width="250" height="{units * 42 + 22}" rx="14" fill="{t["tile"]}" stroke="{t["border"]}"/>')
    for u in range(units):
        uy = y + 16 + u * 42
        out.append(f'<rect x="{x + 16}" y="{uy}" width="218" height="32" rx="7" fill="{t["card"]}" stroke="{t["border"]}"/>')
        for n in range(3):
            color = (t["brand"] if (u * 3 + n) % 5 == 2 else t["ok"]) if live else t["bad"]
            led = f' class="led" style="animation-delay:{((u * 7 + n * 3) % 10) * 0.23:.2f}s"' if live else ' opacity=".45"'
            out.append(f'<circle{led} cx="{x + 36 + n * 16}" cy="{uy + 16}" r="4" fill="{color}"/>')
        for b in range(4):
            out.append(f'<rect x="{x + 118 + b * 26}" y="{uy + 8}" width="18" height="16" rx="3" fill="none" stroke="{t["border"]}"/>')
    color = t["muted"] if live else t["bad"]
    out.append(f'<text class="mono" x="{x + 125}" y="{y + units * 42 + 56}" font-size="15" fill="{color}" text-anchor="middle">{esc(caption)}</text>')
    return "".join(out)


def header(t, box):
    w, h = 1200, 340
    live = box["live"]
    phrases = ["backend-first .NET developer", "I fix backends that fail quietly",
               f"{box['containers']} containers on one Hetzner box" if live else "a homelab on one Hetzner box",
               "and I write down what broke"]
    chips, cx, chip_svg = [("Kyiv, Ukraine", None), ("C# · .NET · ASP.NET Core", None), ("open to contract work", "ok")], 64, []
    for i, (text, dot) in enumerate(chips):
        cw = len(text) * 8.4 + 28 + (16 if dot else 0)
        stroke = t["ok"] if dot else t["border"]
        chip_svg.append(f'<g class="rise" style="animation-delay:{0.5 + i * 0.12:.2f}s">'
                        f'<rect x="{cx}" y="252" width="{cw:.0f}" height="36" rx="18" fill="{t["tile"]}" stroke="{stroke}"/>'
                        + (f'<circle cx="{cx + 20}" cy="270" r="4" fill="{t["ok"]}"/>' if dot else "")
                        + f'<text class="mono" x="{cx + 14 + (16 if dot else 0)}" y="275" font-size="14" fill="{t["fg"]}" '
                          f'textLength="{len(text) * 8.4:.1f}" lengthAdjust="spacing">{esc(text)}</text></g>')
        cx += cw + 12
    caption = f"{box['containers']} containers · {box['unhealthy']} unhealthy" if live else f"silent since {box['since']}"
    edge_def, edge_rect = edge(t, w, h)
    defs = (f'<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="1.5" cy="1.5" r="1.2" fill="{t["border"]}"/></pattern>'
            f'<radialGradient id="glow" cx="84%" cy="12%" r="62%"><stop offset="0" stop-color="{t["brand"]}" stop-opacity=".2"/>'
            f'<stop offset="1" stop-color="{t["brand"]}" stop-opacity="0"/></radialGradient>{edge_def}')
    backdrop = f'<rect width="{w}" height="{h}" fill="url(#dots)"/><rect width="{w}" height="{h}" fill="url(#glow)"/>{edge_rect}'
    body = (f'<text class="mono rise" x="64" y="84" font-size="18" fill="{t["muted"]}"><tspan fill="{t["brand"]}">~</tspan> $ whoami</text>'
            f'<text class="rise" style="animation-delay:.15s" x="62" y="164" font-size="68" font-weight="700" letter-spacing="-1.5" fill="{t["fg"]}">Yehor Hrabovskyi</text>'
            + typing(t, phrases, 64, 218, 26) + "".join(chip_svg) + rack(t, 886, 44, live, caption))
    css = (".cursor { animation: blink 1.05s steps(1) infinite; } @keyframes blink { 50% { opacity: 0; } }"
           ".led { animation: led 2.3s ease-in-out infinite; } @keyframes led { 0%, 100% { opacity: 1; } 50% { opacity: .2; } }")
    return svg(w, h, t, "Yehor Hrabovskyi, backend-first .NET developer", body, css, defs, backdrop)


# ---------------------------------------------------------------- live dashboard

def dashboard(t, box):
    w, h = 1200, 330
    live, out = box["live"], []
    dot = t["ok"] if live else t["bad"]
    out.append(f'<circle cx="54" cy="47" r="6" fill="{dot}"/>')
    if live:
        out.append(f'<circle cx="54" cy="47" r="6" fill="none" stroke="{dot}" stroke-width="2">'
                   '<animate attributeName="r" values="6;17" dur="1.8s" repeatCount="indefinite"/>'
                   '<animate attributeName="opacity" values=".9;0" dur="1.8s" repeatCount="indefinite"/></circle>')
    out.append(title(t, 72, 52, "live from the box" if live else "the box went silent", None if live else "bad"))
    right = f"Hetzner · Nuremberg · read {box['read']}" if live else f"no report since {box['since']}"
    out.append(f'<text class="mono" x="{w - 48}" y="52" font-size="14" fill="{t["muted"]}" text-anchor="end">{esc(right)}</text>')
    tiles = box["tiles"] if live else [("—", "containers running", "", "faint")] + [("—", l, "", "faint") for _, l, _, _ in box["tiles"][1:]]
    tw = (w - 96 - 3 * 16) / 4
    accents = ["ok", "brand", "info", "violet"]
    for i, (value, label, sub, sub_color) in enumerate(tiles):
        x = 48 + i * (tw + 16)
        out.append(f'<g class="rise" style="animation-delay:{0.1 + i * 0.1:.1f}s">'
                   f'<rect x="{x:.1f}" y="78" width="{tw:.1f}" height="124" rx="12" fill="{t["tile"]}" stroke="{t["border"]}"/>'
                   f'<rect x="{x:.1f}" y="96" width="3" height="40" rx="1.5" fill="{t[accents[i]]}"/>'
                   f'<text x="{x + 24:.1f}" y="134" font-size="46" font-weight="700" letter-spacing="-1" fill="{t["fg"]}">{esc(value)}</text>'
                   f'<text x="{x + 24:.1f}" y="164" font-size="16" fill="{t["muted"]}">{esc(label)}</text>'
                   f'<text class="mono" x="{x + 24:.1f}" y="187" font-size="13" fill="{t[sub_color]}">{esc(sub)}</text></g>')
    if live and box["languages"]:
        out.append(title(t, 48, 240, "typed in the last 30 days", "muted"))
        bx, bw, total, x = 48, w - 96, 1.6, 48.0
        out.append(f'<clipPath id="bar"><rect x="{bx}" y="254" width="{bw}" height="12" rx="6"/></clipPath>'
                   f'<rect x="{bx}" y="254" width="{bw}" height="12" rx="6" fill="{t["tile"]}"/><g clip-path="url(#bar)">')
        shares, start = box["languages"], 0.0
        for name, pct in shares:
            sw = bw * pct / 100
            a, b = start / 100 * total, (start + pct) / 100 * total
            out.append(f'<rect x="{x:.1f}" y="254" width="{sw:.1f}" height="12" fill="{LANGUAGE_COLORS.get(name, t["faint"])}">'
                       f'<animate attributeName="width" values="0;0;{sw:.1f}" keyTimes="0;{a / total:.3f};{b / total:.3f}" '
                       f'dur="{total}s" fill="freeze"/></rect>')
            x += sw
            start += pct
        out.append("</g>")
        lx = 48.0
        for name, pct in shares:
            text = f"{name} {pct}%"
            out.append(f'<circle cx="{lx + 5:.1f}" cy="294" r="5" fill="{LANGUAGE_COLORS.get(name, t["faint"])}"/>'
                       f'<text class="mono" x="{lx + 16:.1f}" y="299" font-size="14" fill="{t["muted"]}" '
                       f'textLength="{len(text) * 8.4:.1f}" lengthAdjust="spacing">{esc(text)}</text>')
            lx += len(text) * 8.4 + 46
    elif not live:
        out.append(f'<text x="48" y="262" font-size="17" fill="{t["muted"]}">The cron job on the box stopped writing status.json. '
                   'This card recovers on its own when it starts again.</text>')
    edge_def, edge_rect = edge(t, w, h)
    return svg(w, h, t, box["alt"], "".join(out), defs=edge_def, backdrop=edge_rect)


# ---------------------------------------------------------------- project cards

def card(t, title_text, status, lines, language, tags):
    w, h = 600, 190
    color = t[STATUS_COLOR.get(status, "muted")]
    pill_w = len(status) * 9.6 + 28
    lang_color = LANGUAGE_COLORS.get(language, t["faint"])
    body = (f'<g transform="translate(30 30) scale(1.45)"><path d="{REPO_ICON}" fill="{t["muted"]}"/></g>'
            f'<text x="66" y="52" font-size="27" font-weight="700" fill="{t["fg"]}">{esc(title_text)}</text>'
            f'<rect x="{w - 30 - pill_w:.1f}" y="30" width="{pill_w:.1f}" height="28" rx="14" fill="{color}" fill-opacity=".14" stroke="{color}" stroke-opacity=".55"/>'
            f'<text class="mono" x="{w - 30 - pill_w / 2:.1f}" y="49" font-size="14" letter-spacing="1.5" fill="{color}" text-anchor="middle">{esc(status.upper())}</text>'
            + "".join(f'<text x="30" y="{98 + i * 28}" font-size="19" fill="{t["muted"]}">{esc(line)}</text>' for i, line in enumerate(lines))
            + f'<circle cx="37" cy="159" r="7" fill="{lang_color}"/>'
              f'<text class="mono" x="52" y="165" font-size="16" fill="{t["fg"]}" textLength="{len(language) * 9.6:.1f}" '
              f'lengthAdjust="spacing">{esc(language)}</text>'
              f'<text class="mono" x="{62 + len(language) * 9.6:.1f}" y="165" font-size="15" fill="{t["faint"]}">· {esc(tags)}</text>')
    edge_def, edge_rect = edge(t, w, h)
    return svg(w, h, t, f"{title_text}: {' '.join(lines)}", body, defs=edge_def, backdrop=edge_rect, below=16)


# ---------------------------------------------------------------- stack

def stack(t, icons):
    w = 1200
    row, top = 104, 84
    h = top + len(STACK) * row + 10
    out = [title(t, 48, 52, "what I build with")]
    for r, (group, names) in enumerate(STACK):
        y = top + r * row
        if r:
            out.append(f'<rect x="48" y="{y - 12}" width="{w - 96}" height="1" fill="{t["border"]}"/>')
        out.append(f'<text class="mono" x="48" y="{y + 40}" font-size="15" letter-spacing="1.5" fill="{t["muted"]}">{esc(group.upper())}</text>')
        for i, name in enumerate(names):
            x = 250 + i * 110
            uri = "data:image/svg+xml;base64," + base64.b64encode(icons[name]).decode()
            out.append(f'<g class="rise" style="animation-delay:{0.05 * (r * 8 + i):.2f}s">'
                       f'<image x="{x + 19}" y="{y + 4}" width="52" height="52" href="{uri}"/>'
                       f'<text x="{x + 45}" y="{y + 78}" font-size="14" fill="{t["muted"]}" text-anchor="middle">{esc(ICON_NAMES[name])}</text></g>')
    edge_def, edge_rect = edge(t, w, h)
    return svg(w, h, t, "Stack: " + "; ".join(f"{g}: {', '.join(ICON_NAMES[n] for n in ns)}" for g, ns in STACK),
               "".join(out), defs=edge_def, backdrop=edge_rect)


# ---------------------------------------------------------------- data

def when(iso):
    d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return d, f"{d.day} {d:%b}, {d:%H:%M} UTC"


def read_box(status, feed, now):
    generated, read = when(status["generated"])
    live = (now - generated).total_seconds() / 3600 <= MAX_AGE_HOURS
    coding, package = status.get("coding") or {}, status.get("package") or {}
    langs = [(l["name"], l["percent"]) for l in coding.get("languages") or [] if l["name"] != "Unknown"][:6]
    other = 100 - sum(p for _, p in langs)
    if other > 0:
        langs.append(("other", other))
    posts = sorted(feed["items"], key=lambda i: i["date_published"], reverse=True)
    latest = datetime.fromisoformat(posts[0]["date_published"].replace("Z", "+00:00"))
    unhealthy = status["unhealthy"]
    tiles = [
        (str(status["containers"]), "containers running", f"{unhealthy} unhealthy", "ok" if unhealthy == 0 else "bad"),
        (f"{coding.get('hours', 0)}h", "coded in 30 days", "self-hosted Wakapi", "faint"),
        (f"{package.get('downloads', 0):,}", "NuGet installs", f"{package.get('id', 'Attest')} v{package.get('version', '?')}", "faint"),
        (str(len(posts)), "posts written", f"latest {latest.day} {latest:%b}", "faint"),
    ]
    alt = (f"Live from the box, read {read}: {status['containers']} containers running, {unhealthy} unhealthy; "
           f"{coding.get('hours', 0)} hours coded in 30 days; {package.get('downloads', 0)} NuGet installs; {len(posts)} posts."
           if live else f"The box has not reported since {read}.")
    return dict(live=live, read=read, since=read, containers=status["containers"], unhealthy=unhealthy,
                tiles=tiles, languages=langs, alt=alt, posts=posts)


def write(name, text):
    with open(os.path.join(ASSETS, name), "w", encoding="utf-8") as f:
        f.write(text)


def put(text, name, body):
    pattern = re.compile(rf"(<!-- {name}:start -->\n).*?(<!-- {name}:end -->)", re.S)
    new, n = pattern.subn(lambda m: m.group(1) + body + "\n" + m.group(2), text)
    if n != 1:
        sys.exit(f"README.md has {n} {name} blocks, expected 1")
    return new


def main():
    os.makedirs(ASSETS, exist_ok=True)
    now = datetime.now(timezone.utc)
    status = attempt("status.json", lambda: fetch(f"{SITE}/status.json"))
    feed = attempt("feed.json", lambda: fetch(f"{SITE}/feed.json"))
    with open(README, encoding="utf-8") as f:
        readme = f.read()

    box = read_box(status, feed, now) if status and feed else None
    if box:
        if not box["live"]:
            problems.append(f"status.json is stale: the box has not reported since {box['read']}")
        for theme, t in THEMES.items():
            write(f"header-{theme}.svg", header(t, box))
            write(f"box-{theme}.svg", dashboard(t, box))
        readme = put(readme, "box", f'<picture><source media="(prefers-color-scheme: dark)" srcset="assets/box-dark.svg">'
                                    f'<img alt="{esc(box["alt"])}" src="assets/box-light.svg" width="100%"></picture>')
        readme = put(readme, "posts", "\n".join(
            f"- `{datetime.fromisoformat(p['date_published'].replace('Z', '+00:00')):%d %b}` &nbsp;[{p['title']}]({p['url']})"
            for p in box["posts"][:5]))

    for repo, name, status_text, lines, tags in PROJECTS:
        info = attempt(f"repo {repo}", lambda: fetch(f"https://api.github.com/repos/{repo}"))
        if info is None:
            continue
        slug = repo.split("/")[1].lower()
        for theme, t in THEMES.items():
            write(f"card-{slug}-{theme}.svg", card(t, name, status_text, lines, info.get("language") or "—", tags))

    for theme, t in THEMES.items():
        icons = {}
        for name in {n for _, ns in STACK for n in ns}:
            with open(os.path.join(ASSETS, "icons", f"{name}-{theme}.svg"), "rb") as f:
                icons[name] = f.read()
        write(f"stack-{theme}.svg", stack(t, icons))

    with open(README, "w", encoding="utf-8") as f:
        f.write(readme)
    if out := os.environ.get("GITHUB_OUTPUT"):
        with open(out, "a") as f:
            f.write("problems=" + " | ".join(problems).replace("\n", " ") + "\n")
    for p in problems:
        print("problem:", p, file=sys.stderr)
    print("drawn" + (f" with {len(problems)} problem(s)" if problems else ""))


if __name__ == "__main__":
    main()
