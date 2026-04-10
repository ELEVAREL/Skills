---
name: graphql-patterns
description: GraphQL API design patterns and best practices. Use when building GraphQL APIs, designing schemas, implementing resolvers, or optimizing queries.
---

# GraphQL Patterns

Best practices for building production GraphQL APIs.

## Schema Design

### Naming Conventions
- Types: PascalCase (`User`, `OrderItem`)
- Fields: camelCase (`firstName`, `createdAt`)
- Enums: SCREAMING_SNAKE_CASE (`ORDER_STATUS`, `PAYMENT_METHOD`)
- Mutations: verb + noun (`createUser`, `updateOrder`, `deleteComment`)

### Connection Pattern (Relay-style Pagination)
```graphql
type Query {
  users(first: Int, after: String, last: Int, before: String): UserConnection!
}

type UserConnection {
  edges: [UserEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type UserEdge {
  cursor: String!
  node: User!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}
```

### Input Types for Mutations
```graphql
input CreateUserInput {
  name: String!
  email: String!
  role: UserRole = MEMBER
}

type CreateUserPayload {
  user: User
  errors: [UserError!]!
}

type UserError {
  field: String!
  message: String!
}
```

## Performance

### N+1 Problem → DataLoader
- Use DataLoader to batch and cache database requests
- One DataLoader per request context (not global)
- Batch by primary key for efficient SQL `WHERE id IN (...)`

### Query Complexity
- Implement query cost analysis
- Set maximum depth (typically 7-10)
- Set maximum complexity score
- Reject overly expensive queries before execution

### Persisted Queries
- Pre-register known queries
- Send query hash instead of full query string
- Reduces bandwidth and prevents arbitrary queries

## Security

- **Authentication**: Validate JWT/session in context middleware
- **Authorization**: Field-level permissions in resolvers
- **Rate limiting**: Per-query or per-complexity-unit limits
- **Introspection**: Disable in production
- **Input validation**: Validate all mutation inputs
- **Query depth limiting**: Prevent deeply nested queries

## Error Handling

```graphql
type Mutation {
  createOrder(input: CreateOrderInput!): CreateOrderResult!
}

union CreateOrderResult = CreateOrderSuccess | ValidationError | NotFoundError

type CreateOrderSuccess {
  order: Order!
}

type ValidationError {
  field: String!
  message: String!
}
```

Use union types for expected errors. Reserve GraphQL errors for unexpected failures.
