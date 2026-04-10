---
name: slo-implement
description: Define and implement Service Level Objectives with error budgets, burn rate alerts, and automated responses. Use when establishing reliability targets, SLAs, or SLO-based alerting.
---

# SLO Implementation

Define, measure, and alert on Service Level Objectives.

## Key Concepts

- **SLI** (Service Level Indicator): A quantitative measure of service behavior (e.g., latency, availability)
- **SLO** (Service Level Objective): A target value for an SLI (e.g., 99.9% availability)
- **SLA** (Service Level Agreement): A business contract based on SLOs with consequences
- **Error Budget**: The allowed amount of unreliability (100% - SLO)

## Common SLOs

### Availability
```
SLI: Successful requests / Total requests
SLO: 99.9% over 30 days
Error Budget: 0.1% = ~43 minutes of downtime/month
```

### Latency
```
SLI: Requests served within threshold / Total requests
SLO: 95% of requests < 200ms, 99% < 1000ms
Error Budget: 5% of requests can be slow
```

### Correctness
```
SLI: Correct responses / Total responses
SLO: 99.99% correct responses
Error Budget: 0.01% = ~4.3 minutes of incorrect responses/month
```

## Error Budget Math

| SLO | Monthly Budget | Daily Budget |
|-----|----------------|--------------|
| 99% | 7h 18m | 14m 24s |
| 99.5% | 3h 39m | 7m 12s |
| 99.9% | 43m 50s | 1m 26s |
| 99.95% | 21m 55s | 43s |
| 99.99% | 4m 23s | 8.6s |

## Multi-Window Burn Rate Alerting

Instead of alerting on raw error rates, alert when you're burning error budget too fast:

### Fast Burn (Page)
- **Window**: 1 hour
- **Burn rate**: 14.4x (burns entire monthly budget in 2 days)
- **Action**: Page on-call immediately

### Slow Burn (Ticket)
- **Window**: 6 hours  
- **Burn rate**: 6x (burns entire monthly budget in 5 days)
- **Action**: Create ticket for investigation

### Sustained Burn (Review)
- **Window**: 3 days
- **Burn rate**: 1x (on track to exhaust budget this month)
- **Action**: Review in next planning meeting

## Implementation Steps

1. **Choose SLIs** based on user-facing behavior
2. **Set SLO targets** based on business needs (not aspirational)
3. **Instrument measurement** with counters/histograms
4. **Build dashboard** showing current SLO status and error budget
5. **Configure alerts** using multi-window burn rates
6. **Establish process** for error budget exhaustion

## Error Budget Policy

When the error budget is exhausted:
1. Freeze non-critical feature launches
2. Prioritize reliability work
3. Require extra review for changes
4. Post-mortem on what consumed the budget
5. Resume normal development when budget recovers
