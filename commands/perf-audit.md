---
name: perf-audit
description: Run a performance audit on the codebase
disable-model-invocation: true
---

Perform a comprehensive performance audit of: $ARGUMENTS

1. Scan for N+1 queries and database anti-patterns
2. Check for missing pagination on list endpoints
3. Identify synchronous operations that should be async
4. Look for missing caching opportunities
5. Check frontend bundle size and rendering patterns
6. Report findings with severity and suggested fixes

Use the performance-profiling skill patterns.
Format output as a table with: Location | Issue | Severity | Fix.
