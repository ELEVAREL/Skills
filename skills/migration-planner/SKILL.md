---
name: migration-planner
description: Plan and execute code migrations including framework upgrades, language migrations, database migrations, and API versioning. Use when upgrading major dependencies, migrating between frameworks, or versioning APIs.
---

# Migration Planner

Plan and execute safe migrations with zero downtime.

## 1. Assessment Phase

Before any migration:
- **Inventory**: List all affected files, modules, dependencies
- **Impact analysis**: What breaks if we change this?
- **Dependency chain**: What depends on what we're migrating?
- **Test coverage**: Do we have tests for affected areas?
- **Rollback plan**: How do we undo if it goes wrong?

## 2. Migration Strategies

### Strangler Fig (Preferred)
- Run old and new side-by-side
- Gradually route traffic/calls to new implementation
- Remove old code only after new is fully validated
- Best for: framework migrations, service rewrites

### Big Bang
- Migrate everything at once
- Best for: small codebases, tightly coupled changes
- Requires: comprehensive test coverage, maintenance window

### Branch by Abstraction
- Introduce abstraction layer between old and new
- Swap implementation behind the abstraction
- Best for: library replacements, API changes

### Parallel Run
- Execute both old and new, compare results
- Log discrepancies without affecting users
- Best for: algorithm changes, data processing migrations

## 3. Common Migration Types

### Framework Upgrade (e.g., React 18→19, Next.js 14→15)
1. Read migration guide thoroughly
2. Update dependencies incrementally
3. Fix breaking changes one category at a time
4. Run full test suite after each change
5. Check for deprecated API usage
6. Verify build and bundle size

### Database Migration
1. Write forward migration AND rollback
2. Test with production-like data volume
3. Check for lock-heavy operations (adding NOT NULL columns on large tables)
4. Use online schema change tools for large tables
5. Deploy migration separate from code changes
6. Monitor query performance after migration

### API Versioning
1. Keep old version running (don't break existing clients)
2. Add version prefix to new endpoints
3. Document differences between versions
4. Set deprecation timeline for old version
5. Monitor old version usage for sunset planning

## 4. Safety Checklist

- [ ] Migration plan reviewed by team
- [ ] Rollback procedure documented and tested
- [ ] Feature flags in place for gradual rollout
- [ ] Monitoring alerts configured for migration metrics
- [ ] Communication sent to affected teams/users
- [ ] Database backup taken before schema changes
- [ ] Load testing done on new implementation
- [ ] Canary deployment before full rollout

## 5. Migration Document Template

```markdown
## Migration: [FROM] → [TO]

### Scope
- Files affected: X
- Endpoints affected: X
- Database changes: Y/N

### Strategy: [Strangler Fig / Big Bang / Branch by Abstraction]

### Phases
1. **Phase 1**: [description] — [timeline]
2. **Phase 2**: [description] — [timeline]
3. **Phase 3**: [description] — [timeline]

### Rollback Plan
[How to undo each phase]

### Success Criteria
- [ ] All tests passing
- [ ] No increase in error rate
- [ ] Latency within acceptable range
- [ ] No data loss
```
