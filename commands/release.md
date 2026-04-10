---
name: release
description: Generate release notes from git history
disable-model-invocation: true
---

Generate release notes for: $ARGUMENTS

1. Analyze git log since the last release tag
2. Categorize commits by type (feat, fix, perf, etc.)
3. Identify breaking changes
4. List contributors
5. Generate formatted release notes

Use the release-notes-generator skill patterns.
If no version is specified, generate notes for all commits since the last tag.
