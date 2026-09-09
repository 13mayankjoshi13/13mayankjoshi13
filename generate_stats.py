"""
Self-hosted GitHub Stats card - uses the official GitHub REST API directly
(no third-party demo server), so it never randomly goes down.
"""
import os, json, urllib.request

USERNAME = os.environ.get("GH_USERNAME", "13mayankjoshi13")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

BG1 = "#FFFBF5"
CARD = "#FFFFFF"
CORAL, MINT = "#FF9F7A", "#4FC7AA"
TEXT, MUTED, BORDER = "#4A3B31", "#A89A8A", "#F0E1CF"

def api_get(url):
    req = urllib.request.Request(url, headers={"Authorization": f"bearer {TOKEN}", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.load(resp)

def fetch_stats():
    user = api_get(f"https://api.github.com/users/{USERNAME}")
    followers = user.get("followers", 0)
    public_repos = user.get("public_repos", 0)

    repos = []
    page = 1
    while True:
        batch = api_get(f"https://api.github.com/users/{USERNAME}/repos?per_page=100&page={page}")
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    total_stars = sum(r.get("stargazers_count", 0) for r in repos if not r.get("fork"))
    lang_count = {}
    for r in repos:
        if r.get("fork"):
            continue
        lang = r.get("language")
        if lang:
            lang_count[lang] = lang_count.get(lang, 0) + 1
    top_lang = max(lang_count, key=lang_count.get) if lang_count else "\u2014"

    return followers, public_repos, total_stars, top_lang

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def build_svg(followers, public_repos, total_stars, top_lang):
    W, H = 900, 120
    stats = [
        (str(public_repos), "PUBLIC REPOS"),
        (str(followers), "FOLLOWERS"),
        (str(total_stars), "TOTAL STARS"),
        (top_lang, "TOP LANGUAGE"),
    ]
    col_w = W / 4
    svg = f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="accentGrad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{CORAL}"/><stop offset="100%" stop-color="{MINT}"/>
    </linearGradient>
    <filter id="softShadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="3" stdDeviation="6" flood-color="#4A3B31" flood-opacity="0.10"/>
    </filter>
  </defs>
  <rect x="1" y="1" width="{W-2}" height="{H-2}" rx="22" fill="{CARD}" stroke="{BORDER}" filter="url(#softShadow)"/>

  <circle cx="30" cy="26" r="4" fill="{MINT}">
    <animate attributeName="opacity" values="1;0.3;1" dur="1.8s" repeatCount="indefinite"/>
  </circle>
  <text x="42" y="30" font-family="Segoe UI, sans-serif" font-size="12" font-weight="700" letter-spacing="1" fill="{MUTED}">GITHUB STATS</text>
'''
    for i, (val, label) in enumerate(stats):
        cx = col_w/2 + i*col_w
        svg += f'<text x="{cx}" y="76" text-anchor="middle" font-family="Segoe UI, sans-serif" font-size="28" font-weight="700" fill="url(#accentGrad)">{esc(val)}</text>\n'
        svg += f'<text x="{cx}" y="96" text-anchor="middle" font-family="Segoe UI, sans-serif" font-size="10.5" fill="{MUTED}">{esc(label)}</text>\n'
        if i > 0:
            svg += f'<line x1="{i*col_w}" y1="46" x2="{i*col_w}" y2="98" stroke="{BORDER}"/>\n'
    svg += "</svg>"
    return svg

def main():
    try:
        followers, public_repos, total_stars, top_lang = fetch_stats()
    except Exception as ex:
        print(f"ERROR: {ex}")
        followers, public_repos, total_stars, top_lang = 0, 0, 0, "\u2014"
    svg = build_svg(followers, public_repos, total_stars, top_lang)
    os.makedirs("images", exist_ok=True)
    with open("images/stats.svg", "w") as f:
        f.write(svg)

if __name__ == "__main__":
    main()
