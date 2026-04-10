---
name: microservices-patterns
description: Microservices architecture patterns including service decomposition, inter-service communication, data management, and resilience. Use when designing or refactoring distributed systems.
---

# Microservices Patterns

Design resilient, scalable microservices architectures.

## Service Decomposition

### When to Split
- Team boundaries (Conway's Law)
- Independent deployment needs
- Different scaling requirements
- Different technology requirements
- Bounded contexts from domain-driven design

### When NOT to Split
- Less than 5 developers on the project
- Shared database with tight coupling
- Synchronous dependencies between services
- No clear domain boundaries
- "Because microservices are trendy"

## Communication Patterns

### Synchronous (REST/gRPC)
- Use for: queries, real-time responses
- Always set timeouts
- Implement circuit breakers
- Use service mesh or API gateway

### Asynchronous (Events/Messages)
- Use for: commands, notifications, data sync
- Event-driven: publish facts ("OrderCreated"), subscribers react
- Message queue: point-to-point delivery guarantee
- Prefer async for cross-service writes

### Event Patterns
```
# Event Notification (thin)
{ "type": "order.created", "orderId": "123" }
# Subscriber fetches details if needed

# Event-Carried State Transfer (fat)
{ "type": "order.created", "order": { "id": "123", "items": [...] } }
# Subscriber has all data, no callback needed
```

## Data Management

### Database per Service
- Each service owns its data
- No direct database access across services
- Data duplication is OK (eventual consistency)
- Sync via events

### Saga Pattern (Distributed Transactions)
- **Choreography**: Services react to events (simpler, harder to track)
- **Orchestration**: Central coordinator manages steps (more control)
- Always implement compensating transactions for rollback

### CQRS (Command Query Responsibility Segregation)
- Separate read and write models
- Optimize reads with denormalized views
- Sync via events from write to read model

## Resilience Patterns

### Circuit Breaker
- Closed → Open (after N failures)
- Open → Half-Open (after timeout)
- Half-Open → Closed (if request succeeds)

### Retry with Backoff
```
delay = min(baseDelay * 2^attempt + jitter, maxDelay)
```

### Bulkhead
- Isolate resources per downstream service
- Separate thread pools / connection pools
- Failure in one doesn't exhaust resources for others

### Timeout
- Set timeouts on ALL external calls
- Timeout < circuit breaker threshold
- Include timeout in SLO calculations

## Observability (Critical for Microservices)

- Distributed tracing across all services (OpenTelemetry)
- Structured logging with correlation IDs
- Service mesh for traffic visibility
- Health check endpoints on every service
- Centralized log aggregation
