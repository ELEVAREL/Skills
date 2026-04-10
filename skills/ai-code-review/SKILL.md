---
name: ai-code-review
description: Multi-perspective AI code review covering security, performance, architecture, and maintainability. Use when doing thorough code reviews or auditing code quality.
---

# AI Code Review — Multi-Perspective Analysis

Review code from multiple expert perspectives simultaneously.

## Perspective 1: Security Reviewer

Check for:
- SQL/NoSQL injection vulnerabilities
- XSS (Cross-Site Scripting) vectors
- CSRF (Cross-Site Request Forgery) gaps
- Authentication/authorization bypasses
- Secrets or credentials in code
- Insecure deserialization
- Path traversal vulnerabilities
- SSRF (Server-Side Request Forgery)
- Mass assignment vulnerabilities
- Insecure direct object references (IDOR)

## Perspective 2: Performance Reviewer

Check for:
- N+1 database queries
- Missing database indexes for query patterns
- Unbounded queries (no LIMIT)
- Synchronous operations that should be async
- Missing caching for expensive operations
- Memory leaks (unclosed resources, growing collections)
- Unnecessary data serialization
- Large payload sizes
- Missing pagination

## Perspective 3: Architecture Reviewer

Check for:
- Single Responsibility Principle violations
- Inappropriate coupling between modules
- Layer violations (e.g., controller with business logic)
- Missing abstractions or premature abstractions
- Inconsistency with existing patterns
- God classes or functions
- Circular dependencies
- Proper separation of concerns

## Perspective 4: Maintainability Reviewer

Check for:
- Unclear naming (variables, functions, classes)
- Complex conditional logic that could be simplified
- Magic numbers or strings
- Duplicated logic
- Missing error handling
- Overly complex functions (high cyclomatic complexity)
- Dead code or unnecessary comments
- Test coverage gaps

## Review Output Format

```markdown
## Code Review Summary

### Critical Issues (Must Fix)
| # | File | Line | Category | Issue | Suggestion |
|---|------|------|----------|-------|------------|

### Warnings (Should Fix)
| # | File | Line | Category | Issue | Suggestion |
|---|------|------|----------|-------|------------|

### Suggestions (Nice to Have)
| # | File | Line | Category | Issue | Suggestion |
|---|------|------|----------|-------|------------|

### Positive Observations
- [Good patterns observed]

### Overall Assessment
[Summary: is this safe to merge?]
```

## Rules

- Be specific: reference exact file and line
- Provide fixes, not just complaints
- Acknowledge good patterns
- Prioritize: critical security > bugs > performance > style
- Don't nitpick formatting if a formatter is configured
