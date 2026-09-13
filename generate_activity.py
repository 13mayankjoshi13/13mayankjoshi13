"""
Expanded "Activity Overview" card: mini contribution heatmap,
weekly average, most active weekday, and best single day.
Complements the compact Coding Streak card with more texture.
"""
import os, json, urllib.request, datetime
from collections import defaultdict

USERNAME = os.environ.get("GH_USERNAME", "13mayankjoshi13")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

CARD = "#FFFFFF"
CORAL, MINT = "#FF9F7A", "#4FC7AA"
TEXT, MUTED, BORDER = "#4A3B31", "#A89A8A", "#F0E1CF"
CELL_BG = "#F5EDE3"

def fetch_calendar():
    today = datetime.date.today()
    frm = (today - datetime.timedelta(days=100)).isoformat() + "T00:00:00Z"
    to = today.isoformat() + "T23:59:59Z"
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            weeks { contributionDays { date weekday contributionCount } }
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
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.load(resp)
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = []
    for w in weeks:
        for d in w["contributionDays"]:
            days.append((d["date"], d["weekday"], d["contributionCount"]))
    days.sort(key=lambda x: x[0])
    return days[-70:]

def analyze(days):
    weekday_totals = defaultdict(int)
    weekday_counts = defaultdict(int)
    for date, wd, count in days:
        weekday_totals[wd] += count
        weekday_counts[wd] += 1
    weekday_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    best_wd = max(weekday_totals, key=weekday_totals.get) if weekday_totals else 0
    most_active_day = weekday_names[best_wd]

    total = sum(c for _, _, c in days)
    weeks_span = max(1, len(days) / 7)
    weekly_avg = round(total / weeks_span, 1)

    best_day = max(days, key=lambda x: x[2]) if days else (None, None, 0)

    return most_active_day, weekly_avg, best_day

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def color_for(count, max_c):
    if count == 0:
        return CELL_BG
    t = min(1.0, count / max(1, max_c))
    r = int(255 + (79 - 255) * t)
    g = int(159 + (199 - 159) * t)
    b = int(122 + (170 - 122) * t)
    return f"rgb({r},{g},{b})"

def build_svg(days, most_active_day, weekly_avg, best_day):
    W = 900
    grid_cols = 10
    grid_rows = 7
    cell = 16
    gap = 4
    grid_w = grid_cols * (cell + gap)
    grid_x = W - grid_w - 36
    grid_y = 56

    max_c = max((c for _, _, c in days), default=1) or 1

    svg = f'''<svg width="{W}" height="150" viewBox="0 0 {W} 150" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="accentGrad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{CORAL}"/><stop offset="100%" stop-color="{MINT}"/>
    </linearGradient>
    <filter id="softShadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="3" stdDeviation="6" flood-color="#4A3B31" flood-opacity="0.10"/>
    </filter>
  </defs>
  <rect x="1" y="1" width="{W-2}" height="148" rx="22" fill="{CARD}" stroke="{BORDER}" filter="url(#softShadow)"/>

  <circle cx="30" cy="26" r="4" fill="{MINT}">
    <animate attributeName="opacity" values="1;0.3;1" dur="1.8s" repeatCount="indefinite"/>
  </circle>
  <text x="42" y="30" font-family="Segoe UI, sans-serif" font-size="12" font-weight="700" letter-spacing="1" fill="{MUTED}">ACTIVITY OVERVIEW &#183; LAST 70 DAYS</text>

  <text x="32" y="75" font-family="Segoe UI, sans-serif" font-size="22" font-weight="700" fill="url(#accentGrad)">{esc(most_active_day)}</text>
  <text x="32" y="94" font-family="Segoe UI, sans-serif" font-size="10.5" fill="{MUTED}">MOST ACTIVE DAY</text>

  <text x="32" y="128" font-family="Segoe UI, sans-serif" font-size="22" font-weight="700" fill="{TEXT}">{weekly_avg}</text>
  <text x="32" y="144" font-family="Segoe UI, sans-serif" font-size="10.5" fill="{MUTED}">AVG CONTRIBUTIONS / WEEK</text>

  <text x="220" y="75" font-family="Segoe UI, sans-serif" font-size="22" font-weight="700" fill="{TEXT}">{best_day[2]}</text>
  <text x="220" y="94" font-family="Segoe UI, sans-serif" font-size="10.5" fill="{MUTED}">BEST DAY ({esc(best_day[0] or "-")})</text>
'''
    for i, (date, wd, count) in enumerate(days):
        col = i // 7
        row = i % 7
        x = grid_x + col * (cell + gap)
        y = grid_y + row * (cell + gap)
        svg += f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="4" fill="{color_for(count, max_c)}"/>\n'
    svg += "</svg>"
    return svg

def main():
    try:
        days = fetch_calendar()
        most_active_day, weekly_avg, best_day = analyze(days)
    except Exception as ex:
        print(f"ERROR: {ex}")
        days, most_active_day, weekly_avg, best_day = [], "\u2014", 0, (None, None, 0)
    svg = build_svg(days, most_active_day, weekly_avg, best_day)
    os.makedirs("images", exist_ok=True)
    with open("images/activity.svg", "w") as f:
        f.write(svg)

if __name__ == "__main__":
    main()
