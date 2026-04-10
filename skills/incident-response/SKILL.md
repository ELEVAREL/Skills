---
name: incident-response
description: Production incident response workflow. Use when debugging production outages, service degradation, or critical bugs in live systems. Guides triage, root cause analysis, mitigation, and post-mortem.
disable-model-invocation: true
---

# Incident Response Workflow

When responding to a production incident, follow this structured approach:

## 1. Triage & Classify

- Determine severity: P0 (full outage), P1 (major degradation), P2 (partial impact), P3 (minor issue)
- Identify affected services, users, and business impact
- Check monitoring dashboards, error rates, and recent deployments

## 2. Immediate Mitigation

- Look for recent deployments that correlate with the issue onset
- Consider quick rollback if a deploy is the likely cause
- Check for infrastructure issues (disk, memory, CPU, network)
- Implement temporary mitigations (feature flags, traffic shifting, circuit breakers)

## 3. Root Cause Analysis

- Gather logs from affected services: `grep`, `journalctl`, cloud logging
- Trace request flow through distributed systems
- Check for cascading failures or dependency issues
- Reproduce the issue in a staging environment if possible
- Use bisection to narrow down the offending commit

## 4. Fix & Verify

- Implement the fix with appropriate test coverage
- Deploy to staging first, verify the fix
- Monitor error rates and latency after deploying to production
- Confirm the incident is resolved with stakeholders

## 5. Post-Mortem Document

Generate a post-mortem with:
```
## Incident Summary
- **Date/Time**: [when it happened]
- **Duration**: [how long]
- **Severity**: [P0-P3]
- **Impact**: [what was affected]

## Timeline
- [timestamp]: [event]

## Root Cause
[What actually caused the issue]

## Resolution
[What fixed it]

## Action Items
- [ ] [Preventive measure 1]
- [ ] [Preventive measure 2]

## Lessons Learned
[What we should do differently]
```

When triaging, ALWAYS check these first:
1. Recent deployments (`git log --oneline --since="24 hours ago"`)
2. Error rate spikes in logs
3. Resource exhaustion (disk, memory, connections)
4. External dependency failures
