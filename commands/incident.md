---
name: incident
description: Start a production incident response workflow
disable-model-invocation: true
---

Initiate incident response for: $ARGUMENTS

1. Check recent deployments: `git log --oneline --since="24 hours ago"`
2. Scan for errors in the codebase related to the issue
3. Identify the most likely root cause
4. Suggest immediate mitigation steps
5. Draft a post-mortem template

Use the incident-response skill and incident-commander agent patterns.
Prioritize speed — restore service first, investigate root cause after.
