---
name: monorepo-patterns
description: Monorepo management patterns for Turborepo, Nx, pnpm workspaces, and Lerna. Use when setting up or managing monorepos, shared packages, and workspace configurations.
---

# Monorepo Patterns

Manage multi-package repositories effectively.

## Workspace Structure

```
monorepo/
├── apps/
│   ├── web/            # Next.js frontend
│   ├── api/            # Express backend
│   └── mobile/         # React Native app
├── packages/
│   ├── ui/             # Shared component library
│   ├── config/         # Shared ESLint, TypeScript configs
│   ├── database/       # Shared Prisma client
│   └── utils/          # Shared utility functions
├── package.json        # Root workspace config
├── turbo.json          # Turborepo pipeline config
└── pnpm-workspace.yaml # Workspace packages
```

## Package Manager Setup

### pnpm Workspaces (Recommended)
```yaml
# pnpm-workspace.yaml
packages:
  - 'apps/*'
  - 'packages/*'
```

### npm Workspaces
```json
{
  "workspaces": ["apps/*", "packages/*"]
}
```

## Task Orchestration

### Turborepo
```json
{
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", ".next/**"]
    },
    "test": {
      "dependsOn": ["build"]
    },
    "lint": {},
    "dev": {
      "cache": false,
      "persistent": true
    }
  }
}
```

### Key Concepts
- `^build` means "build my dependencies first"
- Outputs define what gets cached
- Persistent tasks (dev servers) don't cache
- Remote caching for CI speed (Turborepo, Nx Cloud)

## Shared Packages

### Internal Packages
```json
{
  "name": "@repo/ui",
  "main": "./src/index.ts",
  "types": "./src/index.ts",
  "scripts": {
    "build": "tsup src/index.ts --format esm,cjs"
  }
}
```

### Consuming Internal Packages
```json
{
  "dependencies": {
    "@repo/ui": "workspace:*",
    "@repo/utils": "workspace:*"
  }
}
```

## Best Practices

- Keep shared configs in a `packages/config` package
- Use TypeScript project references for fast type checking
- Set up CI to only run affected tasks (changed packages + dependents)
- Use changesets for versioning shared packages
- Pin all dependency versions across the monorepo
- Use `.npmrc` with `shared-workspace-lockfile=true`

## Common Issues

| Issue | Solution |
|-------|----------|
| Slow CI | Use remote caching + affected-only runs |
| Dependency conflicts | Enforce single versions with `pnpm.overrides` |
| Circular deps | Restructure or extract shared package |
| Large git clones | Use shallow clones in CI |
| IDE slowness | Configure TypeScript project references |
