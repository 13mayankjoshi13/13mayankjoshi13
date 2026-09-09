"""
Generates a real coding-streak card from the user's actual GitHub
contribution calendar (official GraphQL API, requires GITHUB_TOKEN).
"""
import os, json, urllib.request, datetime

USERNAME = os.environ.get("GH_USERNAME", "13mayankjoshi13")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

BG1, BG2 = "#FFFBF5", "#FFF3E6"
VIOLET, TEAL = "#FF9F7A", "#4FC7AA"
TEXT, MUTED, BORDER = "#4A3B31", "#A89A8A", "#F0E1CF"

def fetch_calendar():
    today = datetime.date.today()
    frm = (today - datetime.timedelta(days=370)).isoformat() + "T00:00:00Z"
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
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.load(resp)
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = []
    for w in weeks:
        for d in w["contributionDays"]:
            days.append((d["date"], d["contributionCount"]))
    days.sort(key=lambda x: x[0])
    return days

def compute_streaks(days):
    today = datetime.date.today().isoformat()
    # current streak: walk backwards from today (or yesterday if today has 0 so far)
    idx_by_date = {d: c for d, c in days}
    current = 0
    d = datetime.date.today()
    # if today has 0 contributions so far, start counting from yesterday
    if idx_by_date.get(d.isoformat(), 0) == 0:
        d = d - datetime.timedelta(days=1)
    while True:
        key = d.isoformat()
        if idx_by_date.get(key, 0) > 0:
            current += 1
            d -= datetime.timedelta(days=1)
        else:
            break

    longest = 0
    run = 0
    last_active = None
    for date, count in days:
        if count > 0:
            run += 1
            longest = max(longest, run)
            last_active = date
        else:
            run = 0
    return current, longest, last_active

def build_svg(current, longest, last_active):
    W, H = 900, 120
    svg = f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bgGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{BG1}"/><stop offset="100%" stop-color="{BG2}"/>
    </linearGradient>
    <linearGradient id="accentGrad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{VIOLET}"/><stop offset="100%" stop-color="{TEAL}"/>
    </linearGradient>
  </defs>
  <rect x="1" y="1" width="{W-2}" height="{H-2}" rx="18" fill="url(#bgGrad)" stroke="{BORDER}"/>

  <circle cx="30" cy="26" r="4" fill="{TEAL}">
    <animate attributeName="opacity" values="1;0.25;1" dur="1.6s" repeatCount="indefinite"/>
  </circle>
  <text x="42" y="30" font-family="Segoe UI, sans-serif" font-size="12" font-weight="700" letter-spacing="1" fill="{MUTED}">CODING STREAK</text>

  <text x="60" y="80" text-anchor="middle" font-family="Segoe UI, sans-serif" font-size="34" font-weight="700" fill="url(#accentGrad)">{current}</text>
  <text x="60" y="100" text-anchor="middle" font-family="Segoe UI, sans-serif" font-size="10.5" fill="{MUTED}">CURRENT</text>

  <line x1="150" y1="46" x2="150" y2="98" stroke="{BORDER}"/>

  <text x="240" y="80" text-anchor="middle" font-family="Segoe UI, sans-serif" font-size="34" font-weight="700" fill="{TEXT}">{longest}</text>
  <text x="240" y="100" text-anchor="middle" font-family="Segoe UI, sans-serif" font-size="10.5" fill="{MUTED}">LONGEST (1YR)</text>

  <line x1="340" y1="46" x2="340" y2="98" stroke="{BORDER}"/>

  <text x="440" y="72" text-anchor="middle" font-family="Segoe UI, sans-serif" font-size="15" font-weight="700" fill="{TEXT}">{last_active or "&#8212;"}</text>
  <text x="440" y="92" text-anchor="middle" font-family="Segoe UI, sans-serif" font-size="10.5" fill="{MUTED}">LAST ACTIVE</text>

  <text x="{W-40}" y="{H/2+5}" text-anchor="end" font-family="Segoe UI, sans-serif" font-size="11" fill="{MUTED}">{"&#128293; keep it going!" if current > 0 else "start today \u2192"}</text>
</svg>'''
    return svg

def main():
    try:
        days = fetch_calendar()
        current, longest, last_active = compute_streaks(days)
    except Exception as ex:
        print(f"ERROR: {ex}")
        current, longest, last_active = 0, 0, None
    svg = build_svg(current, longest, last_active)
    os.makedirs("images", exist_ok=True)
    with open("images/streak.svg", "w") as f:
        f.write(svg)

if __name__ == "__main__":
    main()
