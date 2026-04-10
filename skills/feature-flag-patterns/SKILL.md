---
name: feature-flag-patterns
description: Implement feature flags for safe deployments, A/B testing, and gradual rollouts. Use when adding toggle-able features, percentage rollouts, or user-targeted experiments.
---

# Feature Flag Patterns

Implement feature flags for controlled feature delivery.

## Flag Types

### Release Flags
- Gate incomplete features behind flags
- Enable trunk-based development
- Deploy code without activating features
- Remove after feature is fully rolled out

### Experiment Flags
- A/B testing with user segmentation
- Measure impact of changes
- Statistical significance before full rollout
- Remove after experiment concludes

### Ops Flags
- Circuit breakers for degraded services
- Kill switches for expensive features
- Load shedding during traffic spikes
- Long-lived, managed by operations team

### Permission Flags
- Feature access based on user plan/tier
- Beta access for specific users
- Geographic feature availability
- Long-lived, part of business logic

## Implementation Pattern

```typescript
// Simple feature flag interface
interface FeatureFlags {
  isEnabled(flag: string, context?: FlagContext): boolean;
  getVariant(flag: string, context?: FlagContext): string;
}

interface FlagContext {
  userId?: string;
  userEmail?: string;
  userPlan?: string;
  percentile?: number; // 0-100, deterministic per user
}

// Usage
if (flags.isEnabled('new-checkout-flow', { userId: user.id })) {
  renderNewCheckout();
} else {
  renderOldCheckout();
}
```

## Rollout Strategy

1. **Internal only** (0%): Team testing
2. **Beta users** (1-5%): Early adopters
3. **Gradual rollout** (10% → 25% → 50% → 100%): Monitor at each step
4. **Full rollout** (100%): Clean up flag

## Best Practices

- Name flags descriptively: `enable-new-search-v2` not `flag-123`
- Set expiration dates on temporary flags
- Track flag count — too many flags adds complexity
- Test both flag states in CI
- Log which flag variant each user sees
- Use consistent hashing for percentage rollouts (same user always gets same variant)
- Clean up flags promptly after full rollout or experiment conclusion

## Anti-Patterns to Avoid

- Nested flag checks (flag within flag)
- Long-lived release flags (should be temporary)
- Flags controlling infrastructure (use config instead)
- Flags without ownership (who decides to remove it?)
- Testing only the "on" path
