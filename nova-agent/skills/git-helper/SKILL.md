---
name: git-helper
version: 0.1.0
description: Git workflow tools — smart commit messages, branch summaries, and PR-ready diffs
author: Nova Agent
tags: [git, vcs, dev]
tools: [git_run, git_smart_commit, git_pr_summary]
triggers: [git, commit, branch, diff, pr, pull request]
personas: [dev-sentinel, nova-default]
---

# Git Helper

Adds three tools to Nova for day-to-day git work:

- **git_run** — run any read-only git subcommand in a target directory
- **git_smart_commit** — stage and commit with an AI-ready message template
- **git_pr_summary** — generate a PR summary of the current branch vs a base branch

## Safety

This skill refuses destructive operations: `reset --hard`, `push --force`, `branch -D`,
`clean -f`, and anything with `--no-verify`. For those, Nova will hand back to the user.
