---
name: testing-strategy
description: Design comprehensive testing strategies including unit, integration, e2e, and property-based testing. Use when planning test coverage, choosing testing frameworks, or building test infrastructure.
---

# Testing Strategy

Design effective testing approaches across the test pyramid.

## The Test Pyramid

```
        /  E2E  \           Few, slow, expensive
       /----------\
      / Integration \       Moderate amount
     /----------------\
    /    Unit Tests     \   Many, fast, cheap
   /--------------------\
```

## Unit Tests

### What to Test
- Pure business logic and calculations
- Data transformations
- Validation rules
- Edge cases and boundary conditions

### What NOT to Test
- Framework behavior (React rendering, Express routing)
- Third-party library internals
- Trivial getters/setters
- Private implementation details

### Best Practices
```javascript
// Good: Test behavior, not implementation
test('calculates order total with discount', () => {
  const order = createOrder([item(10), item(20)]);
  order.applyDiscount(0.1);
  expect(order.total).toBe(27);
});

// Bad: Testing implementation details
test('calls calculateSubtotal then applyDiscountRate', () => {
  // Testing internal method calls = brittle
});
```

## Integration Tests

### What to Test
- API endpoint request/response cycles
- Database queries with real database (or testcontainers)
- Service-to-service communication
- Authentication/authorization flows

### Setup
- Use test databases (Docker/testcontainers)
- Seed minimal data per test
- Clean up after each test (transaction rollback)
- Isolate tests from each other

## End-to-End Tests

### What to Test
- Critical user journeys (signup, purchase, etc.)
- Cross-page navigation flows
- Integration with external services (in staging)

### Best Practices
- Keep E2E tests under 20 (they're slow and flaky)
- Use data-testid attributes for selectors (not CSS classes)
- Wait for elements explicitly (no arbitrary sleeps)
- Run against dedicated test environment

## Property-Based Testing

```javascript
// Instead of testing specific values:
test('sort produces sorted array', () => {
  fc.assert(fc.property(fc.array(fc.integer()), (arr) => {
    const sorted = sort(arr);
    // Properties:
    expect(sorted.length).toBe(arr.length); // same length
    for (let i = 1; i < sorted.length; i++) {
      expect(sorted[i]).toBeGreaterThanOrEqual(sorted[i-1]); // ordered
    }
  }));
});
```

## Test Naming

Use the pattern: `[unit] [behavior] when [condition]`

```
calculateTotal returns 0 when cart is empty
createUser throws ValidationError when email is invalid
OrderService sends confirmation email when order is placed
```

## Coverage Guidelines

| Layer | Target | Focus |
|-------|--------|-------|
| Business logic | 90%+ | Pure functions, domain rules |
| API endpoints | 80%+ | Happy path + error cases |
| UI components | 70%+ | User interactions, conditional rendering |
| Utility functions | 95%+ | Edge cases, boundary values |
| Integration | Key paths | Critical user journeys |
