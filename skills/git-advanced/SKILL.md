---
name: git-advanced
description: Advanced Git workflows and techniques including rebasing, cherry-picking, bisecting, worktrees, and recovery. Use when dealing with complex git scenarios, merge conflicts, or repository maintenance.
---

# Advanced Git Techniques

Master advanced git workflows for complex scenarios.

## Branching Strategies

### Trunk-Based Development (Recommended)
- Single long-lived branch (main)
- Short-lived feature branches (< 2 days)
- Feature flags for incomplete work
- CI/CD on every commit to main

### GitFlow
- main (production), develop (integration)
- feature/*, release/*, hotfix/* branches
- More ceremony, useful for versioned releases

## Advanced Operations

### Interactive Rebase (Cleanup Before PR)
```bash
# Squash last 5 commits into meaningful ones
git rebase -i HEAD~5
# pick, squash, fixup, reword, drop
```

### Cherry-Pick (Selective Commits)
```bash
# Apply specific commit to current branch
git cherry-pick <commit-sha>

# Cherry-pick without committing (stage only)
git cherry-pick --no-commit <commit-sha>
```

### Bisect (Find Bug Introduction)
```bash
git bisect start
git bisect bad                    # Current commit is broken
git bisect good <known-good-sha> # This commit was working
# Git checks out middle commit — test it
git bisect good  # or  git bisect bad
# Repeat until the offending commit is found
git bisect reset
```

### Worktrees (Multiple Branches Simultaneously)
```bash
# Create worktree for another branch
git worktree add ../hotfix-branch hotfix/critical-bug

# List worktrees
git worktree list

# Remove when done
git worktree remove ../hotfix-branch
```

### Stash (Save Work in Progress)
```bash
git stash push -m "WIP: feature X"
git stash list
git stash pop                    # Apply and remove
git stash apply stash@{2}       # Apply specific stash
```

## Recovery

### Undo Last Commit (Keep Changes)
```bash
git reset --soft HEAD~1
```

### Recover Deleted Branch
```bash
git reflog  # Find the commit SHA
git checkout -b recovered-branch <sha>
```

### Recover Lost Commits
```bash
git reflog  # Find orphaned commits
git cherry-pick <sha>
```

### Fix Wrong Branch Commit
```bash
# Committed to main instead of feature branch
git branch feature-branch  # Create branch at current commit
git reset --hard HEAD~1     # Remove from main
git checkout feature-branch # Switch to correct branch
```

## Merge Conflict Resolution

1. Understand BOTH sides of the conflict
2. Don't blindly accept "ours" or "theirs"
3. Test after resolving
4. Use `git rerere` to remember resolutions

```bash
# Enable rerere (reuse recorded resolution)
git config rerere.enabled true
```

## Maintenance

```bash
# Clean up remote-tracking branches
git fetch --prune

# Find large files in history
git rev-list --objects --all | git cat-file --batch-check | sort -k3 -n -r | head

# Verify repository integrity
git fsck
```
