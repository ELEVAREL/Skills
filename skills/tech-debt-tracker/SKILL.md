---
name: tech-debt-tracker
description: Assess and prioritize technical debt. Use when auditing code quality, planning refactoring efforts, or building a technical debt reduction roadmap.
---

# Technical Debt Tracker

Systematically identify, categorize, and prioritize technical debt.

## 1. Detection Patterns

### Code-Level Debt
- **TODO/FIXME/HACK comments**: Scan for unresolved markers
- **Dead code**: Unused functions, unreachable branches, commented-out code
- **Copy-paste duplication**: Similar code blocks across files
- **Long methods**: Functions > 50 lines or cyclomatic complexity > 10
- **God classes/modules**: Files > 500 lines with mixed responsibilities
- **Primitive obsession**: Using strings/ints where domain types belong
- **Missing abstractions**: Same concept repeated differently across codebase

### Architecture-Level Debt
- **Circular dependencies**: Modules importing each other
- **Layer violations**: UI code accessing database directly
- **Missing API boundaries**: Internal implementation details exposed
- **Hardcoded configuration**: Values that should be configurable
- **Inconsistent patterns**: Same thing done differently in different places

### Infrastructure Debt
- **Outdated dependencies**: Major versions behind
- **Missing tests**: Low coverage on critical paths
- **Flaky tests**: Tests that pass/fail randomly
- **Manual processes**: Steps that should be automated
- **Missing documentation**: Undocumented APIs or architecture decisions

## 2. Assessment Matrix

Rate each debt item on:

| Factor | Score 1-5 | Description |
|--------|-----------|-------------|
| **Impact** | How much does this slow development? |  |
| **Risk** | What's the chance of a bug/outage? |  |
| **Effort** | How hard is it to fix? (inverse) |  |
| **Spread** | How many areas does it affect? |  |

**Priority Score** = (Impact + Risk + Spread) / Effort

## 3. Debt Categories

- **Reckless & Deliberate**: "We don't have time for design" → Fix ASAP
- **Prudent & Deliberate**: "Ship now, refactor later" → Schedule it
- **Reckless & Inadvertent**: "What's layering?" → Train + fix
- **Prudent & Inadvertent**: "Now we know how we should have done it" → Evolve

## 4. Report Format

```markdown
## Technical Debt Inventory

### Critical (Fix This Sprint)
| Item | Location | Impact | Effort | Risk |
|------|----------|--------|--------|------|

### High (Fix This Quarter)
| Item | Location | Impact | Effort | Risk |
|------|----------|--------|--------|------|

### Medium (Backlog)
| Item | Location | Impact | Effort | Risk |
|------|----------|--------|--------|------|

### Metrics
- Total TODO/FIXME count: X
- Average cyclomatic complexity: X
- Test coverage on critical paths: X%
- Dependencies with known vulnerabilities: X
- Average dependency staleness: X versions behind
```

## 5. Reduction Strategy

1. **Boy Scout Rule**: Leave code cleaner than you found it
2. **Strangler Fig**: Gradually replace legacy systems
3. **Debt Sprint**: Dedicate 20% of sprint to debt reduction
4. **Refactoring Alongside Features**: Bundle debt fixes with feature work
