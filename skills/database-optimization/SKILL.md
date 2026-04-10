---
name: database-optimization
description: Database performance optimization including query tuning, indexing strategies, connection pooling, and schema design. Use when diagnosing slow queries, optimizing database performance, or designing schemas.
---

# Database Optimization

Optimize database performance across PostgreSQL, MySQL, and MongoDB.

## 1. Query Analysis

### PostgreSQL / MySQL
```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) SELECT ...;
```

### What to Look For
- **Seq Scan** on large tables → needs an index
- **Nested Loop** with large tables → consider hash/merge join
- **Sort** without index → add index on sort column
- **High actual rows vs estimate** → stale statistics, run ANALYZE
- **Disk sorts** → increase work_mem (PostgreSQL)

## 2. Indexing Strategy

### When to Add an Index
- Columns in WHERE clauses (especially with high selectivity)
- Columns in JOIN conditions
- Columns in ORDER BY / GROUP BY
- Composite indexes for multi-column queries (order matters!)

### When NOT to Add an Index
- Columns with low cardinality (boolean, status with 2 values)
- Tables with frequent inserts and rare reads
- Small tables (< 1000 rows) — seq scan is faster

### Index Types
| Type | Use Case |
|------|----------|
| B-tree (default) | Equality, range, sorting |
| Hash | Equality only |
| GIN | Full-text search, JSONB, arrays |
| GiST | Geometric, spatial data |
| BRIN | Large naturally ordered tables (timestamps) |

### Partial Indexes
```sql
CREATE INDEX idx_active_users ON users(email) WHERE active = true;
```

## 3. Connection Pooling

- Use PgBouncer, ProxySQL, or application-level pooling
- Set pool size: `connections = (core_count * 2) + effective_spindle_count`
- Monitor: active connections, idle connections, wait queue
- Use transaction-level pooling for best efficiency

## 4. Common Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| SELECT * | Reads unnecessary data | Select only needed columns |
| N+1 queries | 1 query + N queries per row | Use JOIN or batch load |
| No pagination | Returns all rows | Add LIMIT/OFFSET or cursor |
| LIKE '%term%' | Can't use index | Full-text search or trigram index |
| Implicit type casts | Prevents index usage | Match column types in queries |
| Missing VACUUM | Dead rows slow scans | Enable autovacuum, tune settings |

## 5. Schema Design Tips

- Use appropriate data types (don't store dates as strings)
- Add NOT NULL constraints where applicable
- Use foreign keys for data integrity
- Normalize first, denormalize for measured read performance
- Use UUID or ULID for distributed-friendly primary keys
- Add created_at and updated_at to every table
