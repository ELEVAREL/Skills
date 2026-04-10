---
name: dependency-audit
description: Audit project dependencies for security vulnerabilities, license compliance, outdated versions, and unused packages. Use when reviewing supply chain security or preparing for releases.
---

# Dependency Audit

Comprehensive dependency analysis for security, licensing, and maintenance.

## 1. Security Vulnerability Scan

### npm / Node.js
```bash
npm audit
npx better-npm-audit audit
```

### Python
```bash
pip-audit
safety check
```

### Go
```bash
govulncheck ./...
```

### General
- Check dependencies against CVE databases
- Flag any dependency with known critical/high vulnerabilities
- Check for dependency confusion attack vectors (private package names)

## 2. License Compliance

### Permissive (Generally Safe)
- MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC, Unlicense

### Copyleft (Review Required)
- GPL-2.0, GPL-3.0, AGPL-3.0, LGPL, MPL-2.0

### Red Flags
- No license specified (all rights reserved by default)
- Custom or unusual licenses
- License changes between versions

### Check
- List all transitive dependency licenses
- Flag copyleft licenses in proprietary projects
- Verify license compatibility in the dependency tree

## 3. Outdated Dependencies

### Risk Levels
| Behind | Risk | Action |
|--------|------|--------|
| Patch | Low | Update in next sprint |
| Minor | Medium | Schedule update |
| Major (1+) | High | Plan migration |
| Major (2+) | Critical | Prioritize immediately |
| Unmaintained | Critical | Find alternative |

### Unmaintained Indicators
- No commits in 12+ months
- No response to issues/PRs
- Deprecated notice in README
- Archived repository

## 4. Unused Dependencies

Scan for packages that are installed but never imported:
- Check all import/require statements against `package.json` / `requirements.txt`
- Flag devDependencies used in production code
- Flag production dependencies only used in tests

## 5. Supply Chain Security

- [ ] Lock files committed (package-lock.json, yarn.lock, poetry.lock)
- [ ] Dependencies pinned to exact versions in lock files
- [ ] No `install` scripts running arbitrary code
- [ ] Dependency sources verified (official registries only)
- [ ] No typosquatting risks (common misspellings of popular packages)

## Report Format

```markdown
## Dependency Audit Report

### Summary
- Total dependencies: X (Y direct, Z transitive)
- Vulnerabilities: X critical, Y high, Z moderate
- Outdated: X major, Y minor, Z patch
- License issues: X
- Unused: X

### Critical Issues (Fix Immediately)
| Package | Issue | Severity | Fix |
|---------|-------|----------|-----|

### Action Items
1. [Immediate actions]
2. [Scheduled updates]
3. [Packages to replace]
```
