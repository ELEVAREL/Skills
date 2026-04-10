---
name: release-notes-generator
description: Auto-generate release notes from git history, PRs, and commits. Use when preparing releases, changelogs, or communicating changes to stakeholders.
disable-model-invocation: true
---

# Release Notes Generator

Generate professional release notes from repository history.

## Process

1. **Gather Changes**
   - Parse git log since last release tag
   - Group commits by type (conventional commits)
   - Cross-reference with merged PRs if available
   - Identify breaking changes

2. **Classify Changes**

   | Prefix | Category | Audience |
   |--------|----------|----------|
   | `feat:` | New Features | Users |
   | `fix:` | Bug Fixes | Users |
   | `perf:` | Performance | Users |
   | `docs:` | Documentation | Users |
   | `refactor:` | Internal Changes | Developers |
   | `test:` | Testing | Developers |
   | `ci:` | CI/CD | Developers |
   | `chore:` | Maintenance | Developers |
   | `BREAKING CHANGE:` | Breaking Changes | Everyone |

3. **Generate Notes**

Use this template:

```markdown
# Release vX.Y.Z

**Release Date**: YYYY-MM-DD

## Highlights

[1-3 sentence summary of the most important changes]

## Breaking Changes

- **[Component]**: Description of breaking change and migration path

## New Features

- **[Feature name]**: Brief description (#PR)

## Bug Fixes

- **[Fix description]**: What was broken and how it's fixed (#PR)

## Performance Improvements

- **[Area]**: What improved and by how much (#PR)

## Other Changes

- [Minor changes, dependency updates, etc.]

## Contributors

Thanks to @contributor1, @contributor2 for their contributions!

## Upgrade Guide

[Step-by-step instructions if there are breaking changes]
```

## Git Commands for Input

```bash
# Get commits since last tag
git log $(git describe --tags --abbrev=0)..HEAD --oneline

# Get conventional commit breakdown
git log $(git describe --tags --abbrev=0)..HEAD --format="%s" | sort

# Get contributors
git log $(git describe --tags --abbrev=0)..HEAD --format="%an" | sort -u
```

## Rules

- Write for the audience: users care about features and fixes, not refactors
- Be specific: "Fixed login timeout on slow connections" not "Fixed bug"
- Include PR/issue numbers for traceability
- Highlight breaking changes prominently
- Provide migration instructions for breaking changes
