---
name: performance-profiling
description: System and application performance profiling. Use when diagnosing slow endpoints, memory leaks, CPU bottlenecks, database query performance, or frontend rendering issues.
---

# Performance Profiling

Systematic approach to identifying and resolving performance bottlenecks.

## 1. Identify the Bottleneck Type

- **CPU-bound**: High CPU usage, slow computation
- **I/O-bound**: Waiting on disk, network, or database
- **Memory-bound**: Excessive allocation, GC pressure, memory leaks
- **Concurrency**: Lock contention, thread pool exhaustion
- **Frontend**: Slow rendering, large bundles, layout thrashing

## 2. Backend Profiling

### Database Queries
- Find N+1 queries: look for loops that execute queries
- Check for missing indexes: `EXPLAIN ANALYZE` on slow queries
- Look for full table scans on large tables
- Check connection pool settings and saturation
- Identify unnecessary `SELECT *` — select only needed columns

### API Endpoints
- Measure response times at p50, p95, p99
- Check for synchronous operations that should be async
- Look for unnecessary serialization/deserialization
- Verify caching is used for expensive or repeated operations
- Check for missing pagination on list endpoints

### Memory
- Look for unbounded caches or collections
- Check for event listener leaks (listeners added but never removed)
- Verify streams are properly closed
- Check for large object retention in closures

## 3. Frontend Profiling

### Bundle Size
- Analyze with: `npx webpack-bundle-analyzer` or `npx vite-bundle-visualizer`
- Check for duplicate dependencies
- Verify tree-shaking is working (no full library imports)
- Implement code splitting for routes and heavy components
- Lazy-load below-the-fold content

### Rendering
- Check for unnecessary re-renders (React: `React.memo`, `useMemo`, `useCallback`)
- Avoid layout thrashing (reading then writing DOM in loops)
- Use `will-change` CSS property sparingly for animated elements
- Virtualize long lists (react-window, tanstack-virtual)
- Optimize images: proper sizing, modern formats (WebP/AVIF), lazy loading

### Core Web Vitals
- **LCP** (Largest Contentful Paint): < 2.5s
- **INP** (Interaction to Next Paint): < 200ms
- **CLS** (Cumulative Layout Shift): < 0.1

## 4. Optimization Patterns

### Caching
- HTTP caching headers (`Cache-Control`, `ETag`)
- Application-level caching (Redis, in-memory)
- CDN for static assets
- Database query result caching

### Async / Parallel
- Parallelize independent I/O operations
- Use message queues for non-blocking work
- Implement background jobs for expensive processing
- Use connection pooling for databases and HTTP clients

### Data
- Implement pagination and cursor-based navigation
- Use database indexes strategically
- Denormalize read-heavy data paths
- Compress responses (gzip/brotli)

## Report Format

```
## Performance Audit: [Component/Endpoint]
- **Current**: [measured baseline]
- **Target**: [acceptable threshold]
- **Bottleneck**: [what's slow and why]
- **Fix**: [specific recommendation]
- **Expected Impact**: [estimated improvement]
```
