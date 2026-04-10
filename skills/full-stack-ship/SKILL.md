---
name: full-stack-ship
description: End-to-end feature shipping orchestrator. Combines planning, implementation, testing, code review, PR creation, and deployment preparation into one automated workflow. Use when shipping a complete feature from idea to merge-ready PR.
disable-model-invocation: true
context: fork
---

# Full Stack Ship — Feature Delivery Orchestrator

This is a meta-skill that orchestrates the entire feature delivery lifecycle. When invoked, execute every phase in order.

## Phase 1: Understand & Plan

1. Read the feature request / issue description from $ARGUMENTS
2. Analyze the codebase to understand:
   - Architecture patterns in use
   - Testing patterns and frameworks
   - Coding conventions and style
   - Related existing code
3. Create a detailed implementation plan:
   - Files to create or modify
   - Database changes needed
   - API endpoints to add/modify
   - Frontend components affected
   - Tests to write

## Phase 2: Implement

1. Follow the project's architecture patterns
2. Implement backend changes first (models, services, controllers)
3. Implement frontend changes (components, state, routing)
4. Follow existing naming conventions and code style
5. Add proper error handling
6. Keep changes minimal — don't refactor unrelated code

## Phase 3: Test

1. Write unit tests for new business logic
2. Write integration tests for API endpoints
3. Write component tests for new UI
4. Run the full test suite and fix any failures
5. Check for regressions in existing tests

## Phase 4: Self-Review

Before marking as complete, verify:
- [ ] All tests pass
- [ ] No console.log / print debugging statements
- [ ] No commented-out code
- [ ] No hardcoded secrets or credentials
- [ ] Error handling is appropriate
- [ ] No N+1 queries
- [ ] UI is accessible (labels, keyboard nav, contrast)
- [ ] Breaking changes documented

## Phase 5: Prepare for Review

1. Stage changes with clean, logical commits
2. Write a clear PR description (use pr-enhance skill pattern)
3. Summarize what was done and any trade-offs made
4. Note any follow-up work needed

## Completion Criteria

The feature is "shipped" when:
- All code changes are implemented
- All tests pass
- Self-review checklist is complete
- Changes are committed with descriptive messages
- PR description is ready
