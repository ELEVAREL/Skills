---
name: error-handling-patterns
description: Error handling patterns across languages and frameworks. Use when implementing error handling, custom errors, error boundaries, retry logic, or graceful degradation.
---

# Error Handling Patterns

Implement robust error handling across the stack.

## Principles

1. **Fail fast**: Detect errors early, close to the source
2. **Fail loud**: Log errors with enough context to debug
3. **Fail gracefully**: Show users meaningful messages, not stack traces
4. **Handle at the right level**: Don't catch if you can't handle it
5. **Be specific**: Catch specific errors, not all errors

## Custom Error Classes

### TypeScript/JavaScript
```typescript
class AppError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode: number = 500,
    public isOperational: boolean = true
  ) {
    super(message);
    this.name = this.constructor.name;
  }
}

class NotFoundError extends AppError {
  constructor(resource: string, id: string) {
    super(`${resource} not found: ${id}`, 'NOT_FOUND', 404);
  }
}

class ValidationError extends AppError {
  constructor(public errors: Record<string, string[]>) {
    super('Validation failed', 'VALIDATION_ERROR', 400);
  }
}
```

### Python
```python
class AppError(Exception):
    def __init__(self, message, code, status_code=500):
        super().__init__(message)
        self.code = code
        self.status_code = status_code
```

## API Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": [
      {"field": "email", "message": "Invalid email format"},
      {"field": "name", "message": "Required field"}
    ]
  }
}
```

## Patterns

### Result Type (No Exceptions)
```typescript
type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E };

function divide(a: number, b: number): Result<number> {
  if (b === 0) return { ok: false, error: new Error('Division by zero') };
  return { ok: true, value: a / b };
}
```

### Retry with Backoff
```typescript
async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (attempt === maxRetries) throw error;
      const delay = baseDelay * Math.pow(2, attempt) + Math.random() * 1000;
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}
```

### React Error Boundary
```tsx
class ErrorBoundary extends React.Component<Props, State> {
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }
  componentDidCatch(error: Error, info: ErrorInfo) {
    logError(error, info);
  }
  render() {
    if (this.state.hasError) return <FallbackUI error={this.state.error} />;
    return this.props.children;
  }
}
```

## Anti-Patterns

- Empty catch blocks (swallowing errors silently)
- Catching Exception/Error base class everywhere
- Using errors for flow control
- Returning null instead of throwing/returning Result
- Exposing internal errors to users (stack traces, SQL errors)
- Logging errors without context (no request ID, no user ID)
