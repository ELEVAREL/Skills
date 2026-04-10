---
name: onboard-developer
description: Generate developer onboarding guides for a codebase. Use when a new developer joins, when documenting setup steps, or when creating getting-started guides.
disable-model-invocation: true
---

# Developer Onboarding Guide Generator

Analyze the codebase and generate a comprehensive onboarding guide.

## Analysis Steps

1. **Project Overview**
   - Identify the tech stack from package files, configs, and code
   - Determine the architecture pattern (monolith, microservices, monorepo)
   - Map the directory structure and explain each top-level directory

2. **Setup Instructions**
   - Required tools and versions (Node, Python, Docker, etc.)
   - Environment variables needed (from .env.example or config files)
   - Database setup and seeding
   - Step-by-step "first run" instructions
   - Verify setup: what URL/command confirms it's working

3. **Development Workflow**
   - How to run the dev server
   - How to run tests (unit, integration, e2e)
   - How to run linters and formatters
   - Branch naming convention
   - Commit message convention
   - PR process and review requirements

4. **Architecture Guide**
   - High-level system diagram
   - Key modules and their responsibilities
   - Data flow for the main user journeys
   - Where to find: API routes, database models, business logic, tests

5. **Key Concepts**
   - Domain-specific terminology
   - Important abstractions and patterns used
   - "Why was it built this way?" for non-obvious decisions

## Output Format

```markdown
# [Project Name] - Developer Onboarding

## Quick Start
[5 commands or fewer to get running]

## Tech Stack
[Language, framework, database, key libraries]

## Project Structure
[Annotated directory tree]

## Development
[How to: run, test, lint, build, deploy]

## Architecture
[How the system works at a high level]

## Key Files
[The 10 most important files to read first]

## Common Tasks
[How to: add an endpoint, add a migration, write a test]

## Troubleshooting
[Common setup issues and fixes]
```

## Tips

- Test the setup instructions on a clean environment
- Link to external docs for tools (don't duplicate)
- Include "first task" suggestions for new developers
- Keep it living — outdated docs are worse than no docs
