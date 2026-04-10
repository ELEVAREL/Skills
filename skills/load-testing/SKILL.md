---
name: load-testing
description: Design and generate load tests for APIs and services. Use when creating performance benchmarks, stress tests, or capacity planning tests using tools like k6, Artillery, or wrk.
---

# Load Testing

Design comprehensive load tests to validate system performance and capacity.

## 1. Test Types

### Smoke Test
- Low load (1-5 virtual users)
- Verify system works under minimal load
- Baseline for comparison

### Load Test
- Expected production load
- Sustained for 10-30 minutes
- Validate SLAs and response times

### Stress Test
- Gradually increase beyond expected load
- Find the breaking point
- Observe degradation behavior

### Spike Test
- Sudden burst of traffic
- Test auto-scaling and circuit breakers
- Verify recovery after spike

### Soak Test
- Normal load for extended period (hours)
- Detect memory leaks and resource exhaustion
- Verify stability over time

## 2. k6 Test Template

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 10 },   // Ramp up
    { duration: '5m', target: 10 },   // Steady state
    { duration: '2m', target: 50 },   // Stress
    { duration: '5m', target: 50 },   // Steady stress
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const res = http.get('http://localhost:3000/api/endpoint');
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
  sleep(1);
}
```

## 3. What to Measure

### Response Metrics
- **p50 latency**: Median response time
- **p95 latency**: 95th percentile (what most users experience)
- **p99 latency**: 99th percentile (worst case for most)
- **Error rate**: % of failed requests
- **Throughput**: Requests per second at target load

### System Metrics During Test
- CPU utilization per service
- Memory usage and GC pauses
- Database connection pool usage
- Network I/O and bandwidth
- Disk I/O (if applicable)
- Queue depth (if applicable)

## 4. Test Scenarios

When creating load tests, cover:
1. **Critical user journeys**: Login → Browse → Purchase
2. **API-heavy operations**: Search, filtering, aggregation
3. **Write-heavy operations**: Form submissions, uploads
4. **Concurrent access**: Same resource accessed by many users
5. **Mixed workload**: Realistic blend of read/write operations

## 5. Results Template

```markdown
## Load Test Results

**Date**: YYYY-MM-DD
**Target**: [service/endpoint]
**Duration**: [test duration]
**Peak VUs**: [max virtual users]

### Key Metrics
| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| p95 Latency | <500ms | Xms | PASS/FAIL |
| p99 Latency | <1000ms | Xms | PASS/FAIL |
| Error Rate | <1% | X% | PASS/FAIL |
| Throughput | >100 rps | X rps | PASS/FAIL |

### Observations
- [Notable findings]

### Recommendations
- [Performance improvements needed]
```
