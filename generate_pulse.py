"""
Generates a "Commit Pulse" SVG card - styled like a music player,
but the waveform is real GitHub commit activity from the last N days.
Run inside GitHub Actions where GITHUB_TOKEN and GITHUB_REPOSITORY_OWNER are available.
"""
import os, json, urllib.request, datetime

USERNAME = os.environ.get("GH_USERNAME", "13mayankjoshi13")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
DAYS = 60

NOW_BUILDING = "Open to new opportunities"
if os.path.exists("now-building.txt"):
    with open("now-building.txt") as f:
        val = f.read().strip()
        if val:
            NOW_BUILDING = val

def fetch_contributions():
    today = datetime.date.today()
    frm = (today - datetime.timedelta(days=DAYS+7)).isoformat() + "T00:00:00Z"
    to = today.isoformat() + "T23:59:59Z"
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            weeks { contributionDays { date contributionCount } }
          }
        }
      }
    }
    """
    body = json.dumps({"query": query, "variables": {"login": USERNAME, "from": frm, "to": to}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.load(resp)
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = []
    for w in weeks:
        for d in w["contributionDays"]:
            days.append((d["date"], d["contributionCount"]))
    days.sort(key=lambda x: x[0])
    return [c for _, c in days[-DAYS:]]

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def build_svg(counts):
    W, H = 900, 220

    # Use a real photo if one exists in the repo; fall back to the MJ monogram tile.
    photo_path = None
    for candidate in ("images/profile.jpg", "images/profile.jpeg", "images/profile.png"):
        if os.path.exists(candidate):
            photo_path = os.path.basename(candidate)  # pulse.svg lives in images/ too, so use a same-folder relative reference
            break

    if photo_path:
        avatar_markup = (
            f'<image href="{photo_path}" x="24" y="24" width="{H-48}" height="{H-48}" '
            f'preserveAspectRatio="xMidYMid slice" clip-path="url(#avatarClip)"/>'
        )
    else:
        avatar_markup = (
            f'<rect x="24" y="24" width="{H-48}" height="{H-48}" rx="14" fill="url(#art)"/>'
            f'<text x="{24 + (H-48)/2}" y="{24 + (H-48)/2 + 8}" text-anchor="middle" '
            f'font-family="\'Segoe UI\', sans-serif" font-size="34" font-weight="700" '
            f'fill="#FFFBF5" opacity="0.85">MJ</text>'
        )

    pad_l, pad_r, pad_t, pad_b = 340, 40, 60, 40
    chart_w = W - pad_l - pad_r
    chart_h = H - pad_t - pad_b
    max_c = max(counts) if counts and max(counts) > 0 else 1
    n = len(counts)
    bar_w = chart_w / n * 0.62
    gap = chart_w / n

    bars = []
    for i, c in enumerate(counts):
        h = 6 if c == 0 else max(6, (c / max_c) * chart_h)
        x = pad_l + i * gap
        y = pad_t + (chart_h - h)
        t = i / max(1, n - 1)
        # gradient hue: violet -> teal across the bars
        r = int(255 + (79 - 255) * t)
        g = int(159 + (199 - 159) * t)
        b = int(122 + (170 - 122) * t)
        color = f"rgb({r},{g},{b})"
        bars.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" rx="{bar_w/2:.1f}" fill="{color}"/>')

    total = sum(counts)
    title_size = 26 if len(NOW_BUILDING) <= 16 else max(15, 26 - (len(NOW_BUILDING) - 16) * 0.85)
    svg = f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#FFFBF5"/>
      <stop offset="100%" stop-color="#FFF3E6"/>
    </linearGradient>
    <linearGradient id="art" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#FF9F7A"/>
      <stop offset="100%" stop-color="#4FC7AA"/>
    </linearGradient>
  </defs>
  <rect x="1" y="1" width="{W-2}" height="{H-2}" rx="18" fill="url(#bg)" stroke="#F0E1CF" stroke-width="1"/>

  <clipPath id="avatarClip"><rect x="24" y="24" width="{H-48}" height="{H-48}" rx="14"/></clipPath>
  {avatar_markup}

  <text x="{H-24+16}" y="66" font-family="'Segoe UI', sans-serif" font-size="{title_size:.0f}" font-weight="700" fill="#4A3B31">{esc(NOW_BUILDING)}</text>
  <text x="{H-24+16}" y="92" font-family="'Segoe UI', sans-serif" font-size="14" fill="#A89A8A">Now Building &#183; Live Commit Pulse</text>

  {''.join(bars)}

  <text x="{W-40}" y="{H-16}" text-anchor="end" font-family="'Segoe UI', sans-serif" font-size="11" fill="#B8AA9A">{total} commits &#183; last {n} days</text>
</svg>'''
    return svg

def main():
    try:
        counts = fetch_contributions()
    except Exception as e:
        # fallback: flat low pulse so the card never breaks even if the API call fails
        counts = [1] * DAYS
    svg = build_svg(counts)
    os.makedirs("images", exist_ok=True)
    with open("images/pulse.svg", "w") as f:
        f.write(svg)

if __name__ == "__main__":
    main()
