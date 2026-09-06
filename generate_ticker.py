"""
Generates a continuously-scrolling "Live Activity" ticker SVG,
sourced from the user's real public GitHub events.
Run inside GitHub Actions where GITHUB_TOKEN is available.
"""
import os, json, urllib.request, datetime

USERNAME = os.environ.get("GH_USERNAME", "13mayankjoshi13")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

def fetch_events():
    req = urllib.request.Request(
        f"https://api.github.com/users/{USERNAME}/events/public?per_page=30",
        headers={"Authorization": f"bearer {TOKEN}", "Accept": "application/vnd.github+json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)

def humanize(events):
    items = []
    for e in events:
        t = e["type"]
        repo = e["repo"]["name"].split("/")[-1]
        created = e["created_at"]
        if t == "PushEvent":
            n = len(e["payload"].get("commits", []))
            if n == 0:
                continue
            items.append(f"\u25CF pushed {n} commit{'s' if n != 1 else ''} to {repo}")
        elif t == "CreateEvent" and e["payload"].get("ref_type") == "repository":
            items.append(f"\u25CF created {repo}")
        elif t == "PullRequestEvent":
            action = e["payload"].get("action", "")
            items.append(f"\u25CF {action} a pull request in {repo}")
        elif t == "IssuesEvent":
            action = e["payload"].get("action", "")
            items.append(f"\u25CF {action} an issue in {repo}")
        elif t == "WatchEvent":
            items.append(f"\u25CF starred {repo}")
        elif t == "ForkEvent":
            items.append(f"\u25CF forked {repo}")
        if len(items) >= 8:
            break
    if not items:
        items = ["\u25CF no recent public activity \u2014 check back soon"]
    return items

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def build_svg(items):
    W, H = 900, 56
    text = "     \u2022\u2022\u2022     ".join(items)
    full_text = text + "     \u2022\u2022\u2022     " + text  # duplicate for seamless loop
    # rough width estimate for animation distance
    approx_char_w = 8.4
    seg_width = len(text) * approx_char_w

    svg = f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="tbg" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#120E1E"/>
      <stop offset="50%" stop-color="#1B1330"/>
      <stop offset="100%" stop-color="#120E1E"/>
    </linearGradient>
    <linearGradient id="rfade" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#120E1E" stop-opacity="0"/>
      <stop offset="100%" stop-color="#120E1E" stop-opacity="1"/>
    </linearGradient>
    <clipPath id="clip"><rect x="0" y="0" width="{W}" height="{H}" rx="12"/></clipPath>
  </defs>

  <rect x="0" y="0" width="{W}" height="{H}" rx="12" fill="url(#tbg)"/>

  <g clip-path="url(#clip)">
    <text x="0" y="{H/2+7}" font-family="'Consolas','Courier New',monospace" font-size="15" fill="#38D6C2" letter-spacing="0.3">{esc(full_text)}
      <animate attributeName="x" from="0" to="-{seg_width:.0f}" dur="{max(18, seg_width/45):.0f}s" repeatCount="indefinite"/>
    </text>
  </g>

  <rect x="0" y="0" width="66" height="{H}" fill="#17112A" clip-path="url(#clip)"/>
  <rect x="{W-70}" y="0" width="70" height="{H}" fill="url(#rfade)" clip-path="url(#clip)"/>
  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="#2c2444"/>

  <circle cx="18" cy="{H/2}" r="4" fill="#8B5CF6">
    <animate attributeName="opacity" values="1;0.3;1" dur="1.6s" repeatCount="indefinite"/>
  </circle>
  <text x="30" y="{H/2+4}" font-family="'Segoe UI',sans-serif" font-size="10" fill="#6C6291" letter-spacing="1">LIVE</text>
</svg>'''
    return svg

def main():
    try:
        events = fetch_events()
        items = humanize(events)
    except Exception:
        items = ["\u25CF live feed temporarily unavailable"]
    svg = build_svg(items)
    os.makedirs("images", exist_ok=True)
    with open("images/ticker.svg", "w") as f:
        f.write(svg)

if __name__ == "__main__":
    main()
