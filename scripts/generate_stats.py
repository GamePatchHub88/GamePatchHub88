#!/usr/bin/env python3
"""Generates assets/stats.svg and assets/langs.svg (JavaScript / TypeScript / Python only).
No third-party services and no dependencies - runs inside GitHub Actions.
Usage:  GH_USER=name GITHUB_TOKEN=xxx python scripts/generate_stats.py
        python scripts/generate_stats.py --placeholder   (offline, zeros)
"""
import json, os, sys, urllib.request
from html import escape

USER = os.environ.get("GH_USER", "GamePatchHub88")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
LANGS = [("JavaScript", "#f1e05a"), ("TypeScript", "#3178c6"), ("Python", "#4b8bbe")]
FONT = "'Segoe UI',Ubuntu,Helvetica,Arial,sans-serif"


def api(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-stats"})
    if TOKEN:
        req.add_header("Authorization", "Bearer " + TOKEN)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def collect():
    user = api(f"https://api.github.com/users/{USER}")
    repos, page = [], 1
    while True:
        chunk = api(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner&page={page}")
        repos += chunk
        if len(chunk) < 100:
            break
        page += 1
    bytes_by_lang = {n: 0 for n, _ in LANGS}
    stars = forks = 0
    for r in repos:
        stars += r["stargazers_count"]
        forks += r["forks_count"]
        if r["fork"]:
            continue
        try:
            for lang, b in api(r["languages_url"]).items():
                if lang in bytes_by_lang:
                    bytes_by_lang[lang] += b
        except Exception as e:
            print("skip", r["name"], e)
    return {"repos": user["public_repos"], "followers": user["followers"], "stars": stars,
            "forks": forks, "langs": bytes_by_lang}


def card(w, h, title, body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <rect x="1" y="1" width="{w-2}" height="{h-2}" rx="10" fill="#0d1117" stroke="#30363d" stroke-width="2"/>
  <text x="25" y="38" fill="#58a6ff" font-family="{FONT}" font-size="18" font-weight="600">{escape(title)}</text>
{body}
</svg>
'''


def stats_svg(d):
    rows = [("Public Repos", d["repos"]), ("Total Stars", d["stars"]), ("Total Forks", d["forks"]), ("Followers", d["followers"])]
    body = ""
    for i, (k, v) in enumerate(rows):
        y = 78 + i * 28
        body += (f'  <text x="25" y="{y}" fill="#c9d1d9" font-family="{FONT}" font-size="14">{k}</text>\n'
                 f'  <text x="300" y="{y}" fill="#ffffff" font-family="{FONT}" font-size="14" font-weight="600" text-anchor="end">{v}</text>\n')
    return card(330, 195, f"{USER} - GitHub Stats", body)


def langs_svg(d):
    total = sum(d["langs"].values())
    body = ""
    for i, (name, color) in enumerate(LANGS):
        pct = (d["langs"][name] / total * 100) if total else 0
        y = 70 + i * 36
        bw = 300 * pct / 100
        body += (f'  <text x="25" y="{y}" fill="#c9d1d9" font-family="{FONT}" font-size="14">{name}</text>\n'
                 f'  <text x="325" y="{y}" fill="#8b949e" font-family="{FONT}" font-size="13" text-anchor="end">{pct:.1f}%</text>\n'
                 f'  <rect x="25" y="{y+8}" width="300" height="8" rx="4" fill="#21262d"/>\n'
                 f'  <rect x="25" y="{y+8}" width="0" height="8" rx="4" fill="{color}"><animate attributeName="width" from="0" to="{bw:.1f}" dur="1.2s" fill="freeze"/></rect>\n')
    return card(350, 195, "Top Languages (JS / TS / PY)", body)


if __name__ == "__main__":
    if "--placeholder" in sys.argv:
        data = {"repos": 0, "followers": 0, "stars": 0, "forks": 0, "langs": {n: 0 for n, _ in LANGS}}
    else:
        data = collect()
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, "stats.svg"), "w", encoding="utf-8").write(stats_svg(data))
    open(os.path.join(OUT, "langs.svg"), "w", encoding="utf-8").write(langs_svg(data))
    print("done", data)
