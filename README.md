# Profile Stats

A GitHub Action that automatically keeps your profile README updated with language usage, contribution stats, and recent activity from your public repositories. Private repositories and private activity are never accessed or reflected in the output.

## Prerequisites

Before installing, make sure you have a profile repository, a repo that matches your GitHub username (e.g. `yourname/yourname`). If you don't have one yet:

1. Go to [github.com/new](https://github.com/new)
2. Set the repository name to **your exact GitHub username**
3. Make it **public**
4. Check **Add a README file**
5. Click **Create repository**

### Preview

All stats reflect public repositories and public activity only.

```text
languages                    | stats                        | activity
---------------------------- | ---------------------------- | ----------------------------
python     ████████░░  80.2% | stars                     42 | pushed to myrepo
javascript ██░░░░░░░░  15.1% | issues                     5 | opened pr in webapp
html       █░░░░░░░░░   4.7% | pull requests              8 | starred cool-project
                             | forks                      2 | created repo new-thing
                             | contributions              6 | commented on issue in lib
```

Stats are drawn from public data only and refresh automatically every hour (configurable via cron).

### How It Modifies Your README

The app injects stats between two HTML comment markers:

```
<!-- STATS_START -->
(your stats appear here)
<!-- STATS_END -->
```

- If your README already has these markers, only the content between them is replaced
- If your README doesn't have them, the stats section is appended to the bottom
- If you don't have a README at all, one is created for you
- Everything outside the markers is left untouched, your existing content is safe

## Installation

Add this workflow to your profile repository (`.github/workflows/stats.yml`):

```yaml
name: Update Profile Stats
on:
  schedule:
    - cron: '0 * * * *'  # Runs hourly
  push:
    branches: [main]

jobs:
  update-stats:
    runs-on: ubuntu-latest
    permissions:
      contents: write  # Explicitly allow write access for updates
    steps:
      - uses: 09ball/profile-stats@main
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

### About the `GITHUB_TOKEN`

- `GITHUB_TOKEN` is a special token automatically provided to GitHub Actions. 
- It allows the workflow to authenticate and perform tasks like updating the README in the current repository.
- By default, this token has **limited permissions** and expires when the workflow run finishes.
- Permissions can be explicitly configured in the workflow under the `permissions` section. For this action, write access to `contents` is required.

> [!IMPORTANT]
> Security Note: Always rely on `GITHUB_TOKEN` whenever possible for internal repository automation, as it avoids exposing long-lived personal access tokens or other secret credentials.

## How It Works

| Trigger                 | What Happens                                                                           |
|-------------------------|----------------------------------------------------------------------------------------|
| **Scheduled**           | Workflow runs hourly and updates your profile README with fresh stats                  |
| **Push to profile repo**| Workflow runs immediately, refreshing stats                                            |

The action:
- Counts total stars across all your public repos
- Fetches issues, PRs, and contributions from GitHub GraphQL API
- Detects programming languages from your repos
- Shows your recent public activity
- Updates your profile README between the `<!-- STATS_START -->` and `<!-- STATS_END -->` markers