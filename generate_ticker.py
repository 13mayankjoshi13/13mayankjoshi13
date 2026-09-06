"""
Generates a vertical "Live Activity" list SVG, sourced from the user's
real public GitHub events. Run inside GitHub Actions.
"""
import os, json, urllib.request

USERNAME = os.environ.get("GH_USERNAME", "13mayankjoshi13")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

BG1, BG2 = "#120E1E", "#1B1330"
VIOLET, TEAL = "#8B5CF6", "#38D6C2"
TEXT, MUTED, BORDER = "#F1EAFB", "#9C90C4", "#2c2444"

def fetch_events():
    req = urllib.request.Request(
        f"https://api.github.com/users/{USERNAME}/events/public?per_page=100",
        headers={"Authorization": f"bearer {TOKEN}", "Accept": "application/vnd.github+json"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.load(resp)

def humanize(events):
    items = []
    seen = set()
    for e in events:
        t = e["type"]
        repo = e["repo"]["name"].split("/")[-1]
        line = None
        if t == "PushEvent":
            n = len(e["payload"].get("commits", []))
            if n == 0:
                continue
            line = f"pushed {n} commit{'s' if n != 1 else ''} to {repo}"
        elif t == "CreateEvent" and e["payload"].get("ref_type") == "repository":
            line = f"created {repo}"
        elif t == "PullRequestEvent":
            action = e["payload"].get("action", "")
            line = f"{action} a pull request in {repo}"
        elif t == "IssuesEvent":
            action = e["payload"].get("action", "")
            line = f"{action} an issue in {repo}"
        elif t == "WatchEvent":
            line = f"starred {repo}"
        elif t == "ForkEvent":
            line = f"forked {repo}"
        elif t == "ReleaseEvent":
            line = f"published a release in {repo}"
        if line and line not in seen:
            seen.add(line)
            items.append(line)
        if len(items) >= 6:
            break
    if not items:
        items = ["no recent public activity — check back soon"]
    return items

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def build_svg(items):
    W = 900
    row_h = 34
    top_pad = 46
    H = top_pad + row_h * len(items) + 20

    parts = [f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bgGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{BG1}"/><stop offset="100%" stop-color="{BG2}"/>
    </linearGradient>
  </defs>
  <rect x="1" y="1" width="{W-2}" height="{H-2}" rx="18" fill="url(#bgGrad)" stroke="{BORDER}"/>

  <circle cx="30" cy="26" r="4" fill="{TEAL}">
    <animate attributeName="opacity" values="1;0.25;1" dur="1.6s" repeatCount="indefinite"/>
  </circle>
  <text x="42" y="30" font-family="Segoe UI, sans-serif" font-size="12" font-weight="700" letter-spacing="1" fill="{MUTED}">LIVE ACTIVITY</text>
''']
    for i, item in enumerate(items):
        y = top_pad + i*row_h
        color = TEAL if i % 2 == 0 else VIOLET
        parts.append(f'<circle cx="30" cy="{y+6}" r="3.5" fill="{color}"/>')
        parts.append(f'<text x="46" y="{y+11}" font-family="Consolas, Courier New, monospace" font-size="13.5" fill="{TEXT}">{esc(item)}</text>')
    parts.append("</svg>")
    return "\n".join(parts)

def main():
    try:
        events = fetch_events()
        items = humanize(events)
    except Exception:
        items = ["live feed temporarily unavailable"]
    svg = build_svg(items)
    os.makedirs("images", exist_ok=True)
    with open("images/ticker.svg", "w") as f:
        f.write(svg)

if __name__ == "__main__":
    main()
