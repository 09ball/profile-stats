#!/usr/bin/env python3
"""GitHub Action entrypoint for profile stats."""

import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add repo to path
sys.path.insert(0, os.path.dirname(__file__))

from app.stats import fetch_languages, fetch_activity, fetch_user_stats
from app.readme import generate_output, get_readme_content, push_readme, START_TAG, END_TAG, update_readme_content

def main():
    username = os.environ.get("GITHUB_REPOSITORY_OWNER")
    token = os.environ.get("GITHUB_TOKEN")

    if not username or not token:
        logger.error("GITHUB_REPOSITORY_OWNER and GITHUB_TOKEN env vars required")
        sys.exit(1)

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    logger.info(f"Fetching stats for {username}...")

    lang_data = fetch_languages(username, headers)
    activities = fetch_activity(username, headers)
    stats = fetch_user_stats(username, headers)
    stats_output = generate_output(lang_data, activities, stats)

    logger.info("Updating README...")
    content, sha = get_readme_content(username, headers)

    if content is None:
        new_content = f"# Hi there\n\n{START_TAG}\n{stats_output}\n{END_TAG}\n"
    else:
        new_content = update_readme_content(content, stats_output)

    push_readme(username, headers, new_content, sha=sha)
    logger.info(f"✓ Successfully updated profile stats for {username}")

if __name__ == "__main__":
    main()
