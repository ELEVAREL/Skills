---
name: dep-audit
description: Audit project dependencies for security and compliance
disable-model-invocation: true
---

Audit dependencies for: $ARGUMENTS

1. Check for known vulnerabilities (npm audit, pip-audit, etc.)
2. Verify license compliance
3. Identify outdated dependencies (major versions behind)
4. Find unused dependencies
5. Check for supply chain security issues

Use the dependency-audit skill patterns.
Output a prioritized report with action items.
