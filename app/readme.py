import base64
import logging

import requests

from app.stats import fetch_languages, fetch_activity, fetch_user_stats

logger = logging.getLogger(__name__)
GITHUB_API = "https://api.github.com"

START_TAG = "<!-- STATS_START -->"
END_TAG = "<!-- STATS_END -->"

BOT_NAME = "profile-stats[bot]"
BOT_EMAIL = "profile-stats[bot]@users.noreply.github.com"


def generate_output(lang_data, activities, stats):
    col_width = 28
    sep = "-" * col_width

    lang_col = ["languages", sep]
    for name, bytes_ in lang_data["langs"][:5]:
        perc = (bytes_ / lang_data["total_bytes"]) * 100 if lang_data["total_bytes"] > 0 else 0
        bar = "\u2588" * int(perc / 10) + "\u2591" * (10 - int(perc / 10))
        lang_col.append(f"{name.lower():10} {bar} {perc:5.1f}%")

    stat_col = ["stats", sep]
    entries = [
        ("stars received", str(stats["stars"])),
        ("issues reported", str(stats["issues"])),
        ("pull requests", str(stats["prs"])),
        ("forks received", str(stats["forks"])),
        ("contributions", str(stats["contributed"])),
    ]
    for label, val in entries[:5]:
        stat_col.append(f"{label:<18}{val:>10}")

    act_col = ["activity", sep]
    for a in activities[:5]:
        act_col.append(a[:col_width].lower())

    max_rows = max(len(lang_col), len(stat_col), len(act_col))
    while len(lang_col) < max_rows:
        lang_col.append("")
    while len(stat_col) < max_rows:
        stat_col.append("")
    while len(act_col) < max_rows:
        act_col.append("")

    output = "```text\n"
    for l, s, a in zip(lang_col, stat_col, act_col):
        output += f"{l:<{col_width}} | {s:<{col_width}} | {a:<{col_width}}\n"
    output += "```"
    return output


def get_readme_content(username, headers):
    resp = requests.get(
        f"{GITHUB_API}/repos/{username}/{username}/contents/README.md",
        headers=headers,
    )
    if resp.status_code == 404:
        return None, None
    resp.raise_for_status()
    data = resp.json()
    content = base64.b64decode(data["content"]).decode("utf-8")
    return content, data["sha"]


def update_readme_content(content, stats_output):
    if START_TAG in content and END_TAG in content:
        before = content.split(START_TAG)[0]
        after = content.split(START_TAG)[1].split(END_TAG)[1]
        return f"{before}{START_TAG}\n{stats_output}\n{END_TAG}{after}"
    else:
        return content.rstrip() + f"\n\n{START_TAG}\n{stats_output}\n{END_TAG}\n"


def push_readme(username, headers, new_content, sha=None):
    payload = {
        "message": "Update profile stats",
        "content": base64.b64encode(new_content.encode("utf-8")).decode("ascii"),
        "committer": {
            "name": BOT_NAME,
            "email": BOT_EMAIL,
        },
    }
    if sha:
        payload["sha"] = sha

    resp = requests.put(
        f"{GITHUB_API}/repos/{username}/{username}/contents/README.md",
        headers=headers,
        json=payload,
    )
    resp.raise_for_status()
    return resp.json()


def update_user_readme(username, headers):
    logger.info(f"Updating stats for user: {username}")

    lang_data = fetch_languages(username, headers)
    activities = fetch_activity(username, headers)
    stats = fetch_user_stats(username, headers)
    stats_output = generate_output(lang_data, activities, stats)

    content, sha = get_readme_content(username, headers)

    if content is None:
        new_content = f"# Hi there\n\n{START_TAG}\n{stats_output}\n{END_TAG}\n"
        push_readme(username, headers, new_content)
    else:
        new_content = update_readme_content(content, stats_output)
        push_readme(username, headers, new_content, sha=sha)

    logger.info(f"Successfully updated README for {username}")
