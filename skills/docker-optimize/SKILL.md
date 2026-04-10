---
name: docker-optimize
description: Optimize Docker containers for size, build speed, and security. Use when improving Dockerfiles, reducing image sizes, implementing multi-stage builds, or hardening container security.
---

# Docker Optimization

Optimize Docker images and configurations following these principles:

## 1. Multi-Stage Builds

Always use multi-stage builds to separate build and runtime:
```dockerfile
# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

# Runtime stage
FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
USER node
CMD ["node", "dist/main.js"]
```

## 2. Layer Caching Optimization

- Order instructions from least to most frequently changing
- Copy dependency files before source code
- Use `.dockerignore` to exclude unnecessary files
- Combine related `RUN` commands with `&&` to reduce layers
- Pin base image versions (not `latest`)

## 3. Image Size Reduction

- Use `-alpine` or `-slim` base images
- Remove package manager caches: `rm -rf /var/cache/apk/*`
- Don't install dev dependencies in production images
- Use `--no-install-recommends` for apt-get
- Consider distroless images for maximum reduction

## 4. Security Hardening

- Never run as root: add `USER nonroot` or `USER 1000`
- Don't store secrets in images — use runtime env vars or secrets management
- Scan images: `docker scout cves <image>`
- Use read-only filesystem where possible: `--read-only`
- Drop capabilities: `--cap-drop ALL --cap-add <needed>`
- Set `HEALTHCHECK` instructions

## 5. Docker Compose Optimization

- Use `depends_on` with health checks
- Set resource limits (`mem_limit`, `cpus`)
- Use named volumes for persistent data
- Network isolation between services
- Use `.env` files for environment configuration

## Audit Checklist

When reviewing a Dockerfile, check:
- [ ] Multi-stage build used
- [ ] Base image pinned to specific version
- [ ] .dockerignore present and comprehensive
- [ ] Non-root user configured
- [ ] No secrets in build args or layers
- [ ] HEALTHCHECK defined
- [ ] Layers ordered for optimal caching
- [ ] Unnecessary files excluded from final image
