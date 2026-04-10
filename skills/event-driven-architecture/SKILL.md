---
name: event-driven-architecture
description: Event-driven architecture patterns including event sourcing, CQRS, event buses, and choreography. Use when designing systems with pub/sub, message queues, or event streams.
---

# Event-Driven Architecture

Design event-driven systems with proper patterns and practices.

## Event Types

### Domain Events
- Represent something that happened in the domain
- Named in past tense: `OrderPlaced`, `UserRegistered`, `PaymentProcessed`
- Immutable facts — never modified after creation
- Contain all data needed by consumers

### Integration Events
- Cross service boundary communication
- Versioned for backward compatibility
- Delivered via message broker (RabbitMQ, Kafka, SQS)

### Command Events
- Request for action: `ProcessPayment`, `SendEmail`
- Exactly-once delivery desired
- Single consumer (not broadcast)

## Event Schema

```json
{
  "eventId": "uuid-v4",
  "eventType": "order.placed",
  "eventVersion": "1.0",
  "timestamp": "2026-01-15T10:30:00Z",
  "source": "order-service",
  "correlationId": "request-uuid",
  "data": {
    "orderId": "ord_123",
    "userId": "usr_456",
    "items": [{"sku": "ABC", "qty": 2}],
    "total": 49.99
  }
}
```

## Patterns

### Event Sourcing
- Store events as the source of truth (not current state)
- Rebuild state by replaying events
- Perfect audit trail
- Enables time-travel debugging
- Complex: requires snapshots for performance

### CQRS
- Separate write model (commands) from read model (queries)
- Read models optimized for specific query patterns
- Sync via events
- Enables independent scaling of reads and writes

### Saga (Distributed Transactions)
- **Choreography**: Each service reacts to events from others
- **Orchestration**: Central saga coordinator manages the flow
- Always define compensating actions for rollback

### Outbox Pattern
- Write event to outbox table in same transaction as state change
- Background process publishes from outbox to message broker
- Guarantees at-least-once delivery
- Prevents dual-write problem

## Delivery Guarantees

| Guarantee | Description | Implementation |
|-----------|-------------|----------------|
| At-most-once | Fire and forget | No retries |
| At-least-once | Retry until acknowledged | Idempotent consumers required |
| Exactly-once | Delivered once | Deduplication + at-least-once |

## Consumer Best Practices

- Make consumers idempotent (handle duplicate events)
- Store processed event IDs for deduplication
- Handle out-of-order events gracefully
- Use dead letter queues for failed processing
- Monitor consumer lag
