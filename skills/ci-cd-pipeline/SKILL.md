---
name: ci-cd-pipeline
description: Design and implement CI/CD pipelines for GitHub Actions, GitLab CI, or other platforms. Use when setting up automated builds, tests, deployments, or improving existing pipelines.
---

# CI/CD Pipeline Design

Design efficient, secure CI/CD pipelines.

## GitHub Actions Template

```yaml
name: CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
      - run: npm ci
      - run: npm run lint

  test:
    runs-on: ubuntu-latest
    needs: lint
    strategy:
      matrix:
        node: [18, 20, 22]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node }}
          cache: npm
      - run: npm ci
      - run: npm test -- --coverage
      - uses: actions/upload-artifact@v4
        with:
          name: coverage-${{ matrix.node }}
          path: coverage/

  build:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
      - run: npm ci
      - run: npm run build

  deploy:
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest
    needs: build
    environment: production
    steps:
      - uses: actions/checkout@v4
      - run: echo "Deploy to production"
```

## Best Practices

### Speed
- Cache dependencies (`actions/cache`, `setup-node` with cache)
- Run independent jobs in parallel
- Use `concurrency` to cancel outdated runs
- Only run expensive jobs when relevant files change (path filters)
- Use matrix strategies for multi-version testing

### Security
- Pin action versions to full SHA (not tags)
- Use `GITHUB_TOKEN` with minimal permissions
- Never echo secrets in logs
- Use environment protection rules for production deploys
- Scan for secrets in CI (gitleaks, trufflehog)
- Use OIDC for cloud provider authentication (no long-lived keys)

### Reliability
- Set timeouts on all jobs (`timeout-minutes`)
- Use `retry` for flaky external calls
- Separate build from deploy (deploy is idempotent)
- Keep CI config DRY with reusable workflows
- Test the pipeline itself when modifying it

### Monitoring
- Track CI duration trends
- Alert on consistently failing pipelines
- Monitor flaky test frequency
- Track deployment frequency and lead time

## Pipeline Stages

1. **Lint**: Fast feedback on code style and static analysis
2. **Test**: Unit tests, integration tests (parallelized)
3. **Build**: Compile, bundle, create artifacts
4. **Security**: Dependency audit, SAST scanning
5. **Deploy Staging**: Automated staging deployment
6. **E2E Tests**: Run against staging
7. **Deploy Production**: With approval gate
8. **Smoke Tests**: Verify production deployment
