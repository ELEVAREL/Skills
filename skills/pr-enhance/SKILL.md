---
name: pr-enhance
description: Enhance pull request quality with better descriptions, review suggestions, and context. Use when creating PRs, improving PR descriptions, or preparing code for review.
disable-model-invocation: true
---

# PR Enhancement

Create high-quality pull request descriptions and prepare code for review.

## PR Description Template

```markdown
## What

[1-2 sentences: what this PR does]

## Why

[1-2 sentences: why this change is needed, link to issue/ticket]

## How

[Brief technical approach - what strategy was used]

## Changes

- [Key change 1]
- [Key change 2]
- [Key change 3]

## Testing

- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing done: [describe scenario]

## Screenshots

[If UI changes, before/after screenshots]

## Rollback Plan

[How to revert if something goes wrong]
```

## PR Self-Review Checklist

Before requesting review, verify:

### Code Quality
- [ ] No TODO/FIXME left (unless tracked in issue)
- [ ] No commented-out code
- [ ] No debugging statements (console.log, print, etc.)
- [ ] Error handling is appropriate
- [ ] No hardcoded values that should be config

### Security
- [ ] No secrets or credentials in code
- [ ] Input validation on user-facing endpoints
- [ ] SQL/NoSQL injection prevention
- [ ] XSS prevention for rendered content
- [ ] CSRF protection for state-changing endpoints

### Performance
- [ ] No N+1 queries introduced
- [ ] Large datasets paginated
- [ ] Expensive operations cached or batched
- [ ] No memory leaks (event listeners cleaned up)

### Testing
- [ ] Happy path tested
- [ ] Edge cases tested
- [ ] Error cases tested
- [ ] Test names describe behavior, not implementation

### Documentation
- [ ] Public API changes documented
- [ ] Breaking changes noted in description
- [ ] Complex logic has explanatory comments

## Commit Hygiene

- Each commit represents one logical change
- Commit messages follow conventional commits
- No "fix typo" or "WIP" commits (squash these)
- Commits tell a story when read in order

## Size Guidelines

- **Ideal**: < 300 lines changed
- **Acceptable**: 300-500 lines
- **Too large**: > 500 lines — split into smaller PRs
- Exception: Generated code, migrations, large refactors with mechanical changes
