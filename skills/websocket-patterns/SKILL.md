---
name: websocket-patterns
description: WebSocket implementation patterns for real-time features. Use when building chat, live updates, collaborative editing, notifications, or other real-time communication.
---

# WebSocket Patterns

Implement reliable real-time communication.

## Architecture Patterns

### 1. Pub/Sub (Most Common)
- Clients subscribe to channels/topics
- Server broadcasts to subscribers
- Use cases: chat rooms, live feeds, notifications
- Scale with Redis Pub/Sub or similar message broker

### 2. Request/Response over WS
- Client sends request, server sends response
- Lower latency than HTTP for frequent small requests
- Use JSON-RPC or similar protocol

### 3. Streaming
- Server pushes continuous data to client
- Use cases: real-time metrics, log streaming, live scores
- Consider Server-Sent Events (SSE) if one-directional

## Implementation Checklist

### Connection Management
- [ ] Authentication on connection (validate token in handshake)
- [ ] Heartbeat/ping-pong to detect stale connections
- [ ] Reconnection with exponential backoff on client
- [ ] Connection limit per user
- [ ] Graceful disconnect handling

### Message Protocol
```json
{
  "type": "message",
  "channel": "room:123",
  "payload": { "text": "Hello" },
  "id": "msg_abc123",
  "timestamp": "2026-01-15T10:30:00Z"
}
```

### Error Handling
- Send structured error messages to client
- Don't crash the server on malformed messages
- Rate limit messages per connection
- Validate message size (set max payload)

### Scaling
- Use sticky sessions or a shared message broker
- Redis Pub/Sub for multi-server message distribution
- Consider connection-based horizontal scaling
- Monitor: active connections, messages/sec, memory per connection

## Client-Side Best Practices

```javascript
class WebSocketClient {
  constructor(url) {
    this.url = url;
    this.reconnectDelay = 1000;
    this.maxReconnectDelay = 30000;
    this.connect();
  }

  connect() {
    this.ws = new WebSocket(this.url);
    this.ws.onopen = () => { this.reconnectDelay = 1000; };
    this.ws.onclose = () => { this.reconnect(); };
    this.ws.onerror = () => { this.ws.close(); };
  }

  reconnect() {
    setTimeout(() => {
      this.reconnectDelay = Math.min(
        this.reconnectDelay * 2,
        this.maxReconnectDelay
      );
      this.connect();
    }, this.reconnectDelay);
  }
}
```

## When NOT to Use WebSockets

- One-directional server→client: Use **SSE** (simpler, auto-reconnect)
- Infrequent updates: Use **polling** (simpler infrastructure)
- Request/response only: Use **HTTP/2** (multiplexed, better caching)
- Behind restrictive firewalls: Use **long-polling** (fallback)
