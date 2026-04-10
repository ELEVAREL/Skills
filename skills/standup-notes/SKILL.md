---
name: standup-notes
description: Generate daily standup notes from git activity, PR status, and current work. Use when preparing for standups, writing status updates, or tracking daily progress.
disable-model-invocation: true
---

# Standup Notes Generator

Generate concise standup notes from recent activity.

## Data Sources

Gather information from:

1. **Git log** (last 24 hours):
   ```bash
   git log --oneline --since="24 hours ago" --author="$(git config user.name)"
   ```

2. **Branch status**:
   ```bash
   git branch --show-current
   git status --short
   ```

3. **Recent PRs** (if gh CLI available):
   ```bash
   gh pr list --author=@me --state=all --limit=5
   ```

## Output Format

```markdown
## Standup - [Date]

### Yesterday
- [Completed work item 1]
- [Completed work item 2]
- Merged PR: [title] (#number)

### Today
- [Planned work item 1]
- [Planned work item 2]
- Continue: [ongoing task]

### Blockers
- [Any blockers or dependencies]
- [Items waiting on others]
```

## Rules

- Keep each bullet to one line
- Focus on outcomes, not activities ("Shipped user auth" not "Worked on auth code")
- Mention PR numbers for traceability
- Be honest about blockers — they're opportunities for the team to help
- If no blockers, say "None" (don't skip the section)
- Include context for non-obvious items
