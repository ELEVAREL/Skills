---
name: chaos-engineering
description: Design chaos engineering experiments to test system resilience. Use when validating fault tolerance, circuit breakers, retry logic, graceful degradation, and disaster recovery.
---

# Chaos Engineering

Design experiments to build confidence in system resilience.

## Principles

1. **Start with a hypothesis**: "If X fails, the system should Y"
2. **Minimize blast radius**: Start small, expand gradually
3. **Run in production** (when safe): Staging doesn't catch everything
4. **Automate experiments**: Make them repeatable and measurable

## Experiment Categories

### Network Failures
- **Latency injection**: Add 500ms-5s delay to service calls
- **Packet loss**: Drop X% of network traffic
- **DNS failure**: Simulate DNS resolution failures
- **Connection timeout**: Block outbound connections
- **Partition**: Isolate a service from its dependencies

### Service Failures
- **Process kill**: Terminate a service instance
- **Resource exhaustion**: Fill disk, consume memory/CPU
- **Dependency unavailable**: Stop a downstream service
- **Slow dependency**: Add latency to database or API calls
- **Error injection**: Force errors from a dependency

### Infrastructure Failures
- **Instance termination**: Kill a VM/container
- **Zone failure**: Simulate availability zone outage
- **Database failover**: Trigger primary→replica promotion
- **Cache flush**: Clear all cached data
- **Certificate expiry**: Simulate expired TLS cert

## Experiment Template

```markdown
## Chaos Experiment: [Name]

### Hypothesis
If [failure condition], then [expected behavior].
The system should [graceful degradation behavior].
Users should see [acceptable user experience].

### Steady State
- Error rate: < X%
- Latency p95: < Xms
- Throughput: > X rps

### Method
1. Observe steady state metrics
2. Inject failure: [specific action]
3. Observe system behavior for [duration]
4. Remove failure injection
5. Observe recovery

### Abort Conditions
Stop the experiment if:
- Error rate exceeds X%
- Latency exceeds Xms
- Customer-facing impact detected

### Results
- **Hypothesis confirmed?**: Yes/No
- **Recovery time**: X seconds
- **Unexpected behaviors**: [findings]
- **Action items**: [improvements needed]
```

## Resilience Patterns to Verify

- **Circuit breakers**: Open after X failures, half-open after timeout
- **Retry with backoff**: Exponential backoff with jitter
- **Timeouts**: All external calls have appropriate timeouts
- **Bulkheads**: Failure in one area doesn't cascade
- **Fallbacks**: Degraded but functional experience when dependencies fail
- **Health checks**: Accurate reporting of service health
- **Graceful shutdown**: In-flight requests complete before termination

## Pre-Experiment Checklist

- [ ] Hypothesis documented
- [ ] Abort conditions defined
- [ ] Monitoring dashboards ready
- [ ] Rollback plan in place
- [ ] Team notified
- [ ] Blast radius limited (start with non-critical services)
- [ ] Customer impact minimized (off-peak hours if in production)
