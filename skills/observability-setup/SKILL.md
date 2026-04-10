---
name: observability-setup
description: Set up application observability with metrics, logging, tracing, and alerting. Use when implementing monitoring, setting up dashboards, configuring alerts, or adding OpenTelemetry instrumentation.
---

# Observability Setup

Implement the three pillars of observability: metrics, logs, and traces.

## 1. Structured Logging

### Best Practices
- Use JSON structured logging (not plaintext)
- Include correlation IDs in every log entry
- Log at appropriate levels: ERROR (failures), WARN (degradation), INFO (state changes), DEBUG (troubleshooting)
- Never log secrets, tokens, passwords, or PII
- Include context: request ID, user ID, operation name

### Standard Log Fields
```json
{
  "timestamp": "2026-01-15T10:30:00Z",
  "level": "error",
  "message": "Payment processing failed",
  "service": "payment-service",
  "trace_id": "abc123",
  "span_id": "def456",
  "user_id": "usr_789",
  "error": {
    "type": "PaymentDeclined",
    "message": "Insufficient funds"
  },
  "duration_ms": 234
}
```

## 2. Metrics (RED & USE Methods)

### RED Method (Request-driven services)
- **Rate**: Requests per second
- **Errors**: Failed requests per second
- **Duration**: Response time distribution (p50, p95, p99)

### USE Method (Resources)
- **Utilization**: % time resource is busy
- **Saturation**: Queue depth / backlog
- **Errors**: Error count

### Key Metrics to Instrument
- HTTP request duration (histogram)
- HTTP request count by status code (counter)
- Active connections / in-flight requests (gauge)
- Database query duration (histogram)
- Cache hit/miss ratio (counter)
- Queue depth and processing time (gauge/histogram)
- Business metrics: signups, orders, revenue (counter)

## 3. Distributed Tracing (OpenTelemetry)

### What to Trace
- All incoming HTTP/gRPC requests
- Database queries
- External API calls
- Message queue publish/consume
- Cache operations
- Significant internal operations

### Trace Context
- Propagate trace context across service boundaries
- Use W3C Trace Context headers
- Set meaningful span names: `GET /api/users/{id}` not `HTTP GET`
- Add relevant attributes: `user.id`, `order.id`, `db.statement`

## 4. Alerting

### Alert Design
- Alert on symptoms (high error rate) not causes (CPU high)
- Use multi-window, multi-burn-rate alerts for SLOs
- Set appropriate severity levels and routing
- Include runbook links in every alert

### Essential Alerts
- Error rate > X% for Y minutes
- Latency p99 > threshold
- Service health check failing
- Disk space > 80%
- Certificate expiring within 14 days
- Deployment failed

## 5. Dashboards

### Service Dashboard Template
1. **Overview**: Request rate, error rate, latency p50/p95/p99
2. **Errors**: Error breakdown by type, top error messages
3. **Dependencies**: Downstream service health and latency
4. **Resources**: CPU, memory, disk, network
5. **Business**: Key business metrics specific to the service
