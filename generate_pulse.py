"""
Generates a "Commit Pulse" SVG card - styled like a music player,
but the waveform is real GitHub commit activity from the last N days.
Run inside GitHub Actions where GITHUB_TOKEN and GITHUB_REPOSITORY_OWNER are available.
"""
import os, json, urllib.request, datetime

USERNAME = os.environ.get("GH_USERNAME", "13mayankjoshi13")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
DAYS = 60

NOW_BUILDING = "Ruhanix Bus Booking"
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
    pad_l, pad_r, pad_t, pad_b = 200, 40, 60, 40
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
        r = int(139 + (56 - 139) * t)
        g = int(92 + (214 - 92) * t)
        b = int(246 + (194 - 246) * t)
        color = f"rgb({r},{g},{b})"
        bars.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" rx="{bar_w/2:.1f}" fill="{color}"/>')

    total = sum(counts)
    svg = f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#120E1E"/>
      <stop offset="100%" stop-color="#1B1330"/>
    </linearGradient>
    <linearGradient id="art" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#8B5CF6"/>
      <stop offset="100%" stop-color="#38D6C2"/>
    </linearGradient>
  </defs>
  <rect x="1" y="1" width="{W-2}" height="{H-2}" rx="18" fill="url(#bg)" stroke="#2c2444" stroke-width="1"/>

  <rect x="24" y="24" width="{H-48}" height="{H-48}" rx="14" fill="url(#art)"/>
  <text x="{24 + (H-48)/2}" y="{24 + (H-48)/2 + 8}" text-anchor="middle" font-family="'Segoe UI', sans-serif" font-size="34" font-weight="700" fill="#120E1E" opacity="0.85">MJ</text>

  <text x="{H-24+16}" y="66" font-family="'Segoe UI', sans-serif" font-size="26" font-weight="700" fill="#F1EAFB">{esc(NOW_BUILDING)}</text>
  <text x="{H-24+16}" y="92" font-family="'Segoe UI', sans-serif" font-size="14" fill="#9C90C4">Now Building &#183; Live Commit Pulse</text>

  {''.join(bars)}

  <text x="{W-40}" y="{H-16}" text-anchor="end" font-family="'Segoe UI', sans-serif" font-size="11" fill="#6C6291">{total} commits &#183; last {n} days</text>
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
