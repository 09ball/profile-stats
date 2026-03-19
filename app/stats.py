import logging
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)
GITHUB_API = "https://api.github.com"

_CONTRIBUTIONS_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      totalIssueContributions
      totalPullRequestContributions
      totalRepositoriesWithContributedCommits
    }
  }
}
"""


def fetch_languages(username, headers):
    resp = requests.get(
        f"{GITHUB_API}/users/{username}/repos?per_page=100",
        headers=headers,
    )
    resp.raise_for_status()
    repos = resp.json()

    lang_data = {}
    total_bytes = 0
    for r in repos[:30]:
        lang_resp = requests.get(r["languages_url"], headers=headers)
        if lang_resp.status_code != 200:
            continue
        langs = lang_resp.json()
        if isinstance(langs, dict):
            for lang, byte_count in langs.items():
                lang_data[lang] = lang_data.get(lang, 0) + byte_count
                total_bytes += byte_count

    return {
        "langs": sorted(lang_data.items(), key=lambda x: x[1], reverse=True)[:5],
        "total_bytes": total_bytes,
    }


def fetch_activity(username, headers):
    resp = requests.get(
        f"{GITHUB_API}/users/{username}/events/public?per_page=100",
        headers=headers,
    )
    resp.raise_for_status()
    events = resp.json()

    activities = []
    seen = set()
    for e in events:
        if len(activities) >= 5:
            break
        etype = e.get("type", "")
        repo = e.get("repo", {}).get("name", "").split("/")[-1]
        payload = e.get("payload", {})
        desc = None

        if etype == "PushEvent":
            desc = f"Pushed to {repo}"
        elif etype == "PullRequestEvent":
            action = payload.get("action", "")
            desc = f"{action.capitalize()} PR in {repo}"
        elif etype == "IssuesEvent":
            action = payload.get("action", "")
            desc = f"{action.capitalize()} issue in {repo}"
        elif etype == "CreateEvent":
            ref_type = payload.get("ref_type", "")
            if ref_type == "repository":
                desc = f"Created repo {repo}"
            elif ref_type == "branch":
                desc = f"Created branch in {repo}"
        elif etype == "PullRequestReviewEvent":
            desc = f"Reviewed PR in {repo}"
        elif etype == "WatchEvent":
            desc = f"Starred {repo}"
        elif etype == "ForkEvent":
            desc = f"Forked {repo}"
        elif etype == "IssueCommentEvent":
            desc = f"Commented on issue in {repo}"
        elif etype == "DeleteEvent":
            ref_type = payload.get("ref_type", "")
            desc = f"Deleted {ref_type} in {repo}"

        if desc and desc not in seen:
            seen.add(desc)
            activities.append(desc)
    return activities


def fetch_user_stats(username, headers):
    stars = 0
    page = 1
    while True:
        repos_resp = requests.get(
            f"{GITHUB_API}/users/{username}/repos?per_page=100&page={page}",
            headers=headers,
        )
        repos_resp.raise_for_status()
        repos = repos_resp.json()
        if not repos:
            break
        stars += sum(r.get("stargazers_count", 0) for r in repos)
        if len(repos) < 100:
            break
        page += 1

    user_resp = requests.get(f"{GITHUB_API}/users/{username}", headers=headers)
    user_resp.raise_for_status()
    created_at = user_resp.json()["created_at"]
    start_year = int(created_at[:4])
    current_year = datetime.now(timezone.utc).year

    issues = prs = contributed = 0

    for year in range(start_year, current_year + 1):
        resp = requests.post(
            f"{GITHUB_API}/graphql",
            headers=headers,
            json={
                "query": _CONTRIBUTIONS_QUERY,
                "variables": {
                    "login": username,
                    "from": f"{year}-01-01T00:00:00Z",
                    "to": f"{year}-12-31T23:59:59Z",
                },
            },
        )
        resp.raise_for_status()
        data = resp.json()
        if "errors" in data:
            logger.error(f"GraphQL errors for {username} year {year}: {data['errors']}")
            raise RuntimeError(f"GraphQL errors: {data['errors']}")
        cc = data["data"]["user"]["contributionsCollection"]
        issues += cc["totalIssueContributions"]
        prs += cc["totalPullRequestContributions"]
        contributed += cc["totalRepositoriesWithContributedCommits"]

    return {
        "stars": stars,
        "issues": issues,
        "prs": prs,
        "forks": 0,
        "contributed": contributed,
    }
