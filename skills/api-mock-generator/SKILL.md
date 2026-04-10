---
name: api-mock-generator
description: Generate API mocks for REST, GraphQL, gRPC, and WebSocket protocols. Use when building frontend against unavailable backends, writing integration tests, or prototyping APIs.
---

# API Mock Generator

Generate realistic API mocks with proper data types, edge cases, and error scenarios.

## REST API Mocks

When generating REST mocks:

1. **Analyze the API spec** (OpenAPI/Swagger if available, or infer from code)
2. **Generate mock data** that is realistic, not placeholder:
   - Names should be plausible (not "John Doe" or "Test User")
   - Dates should be recent and logical
   - IDs should follow the project's format (UUID, incremental, etc.)
   - Relationships should be consistent across endpoints

3. **Include edge cases**:
   - Empty collections (`[]`)
   - Null/optional fields
   - Maximum length strings
   - Unicode characters
   - Pagination boundaries

4. **Mock error responses**:
   - 400 Bad Request with validation errors
   - 401 Unauthorized
   - 403 Forbidden
   - 404 Not Found
   - 409 Conflict
   - 429 Rate Limited
   - 500 Internal Server Error

## GraphQL Mocks

- Mock resolvers for each query and mutation
- Include relay-style pagination (edges, nodes, pageInfo)
- Mock subscription events
- Handle partial errors (some fields resolve, some error)

## Mock Server Patterns

### Express/Node
```javascript
// Simple mock server
app.get('/api/users', (req, res) => {
  const page = parseInt(req.query.page) || 1;
  const limit = parseInt(req.query.limit) || 20;
  res.json({
    data: generateUsers(limit),
    meta: { page, limit, total: 100 }
  });
});
```

### MSW (Mock Service Worker)
```javascript
// Browser/Node interception
import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('/api/users', () => {
    return HttpResponse.json({ data: mockUsers });
  }),
];
```

## Data Generation Rules

- Use consistent seed data for reproducibility
- Generate relationships between entities (user -> posts -> comments)
- Include realistic timestamps (created_at < updated_at)
- Vary data (not all records identical)
- Include edge cases: very long names, special characters, empty arrays

## Output

Generate both:
1. **Mock data files** (JSON fixtures)
2. **Mock server code** (runnable mock that serves the fixtures)
3. **Test helpers** (factory functions for generating test data)
