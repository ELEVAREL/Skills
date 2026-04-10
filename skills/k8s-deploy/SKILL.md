---
name: k8s-deploy
description: Generate and review Kubernetes manifests. Use when creating deployments, services, ingress configs, HPA, RBAC, network policies, and other K8s resources.
---

# Kubernetes Manifest Generation

Generate production-ready Kubernetes manifests following best practices.

## Core Resources

### Deployment
- Set resource requests AND limits for all containers
- Use `readinessProbe` and `livenessProbe` (with appropriate thresholds)
- Set `revisionHistoryLimit` to limit old ReplicaSets
- Use `PodDisruptionBudget` for high-availability workloads
- Set `securityContext`: `runAsNonRoot: true`, `readOnlyRootFilesystem: true`
- Use labels consistently: `app`, `version`, `component`, `managed-by`

### Service
- Use `ClusterIP` for internal services
- Use `LoadBalancer` or `Ingress` for external access
- Set `targetPort` to named port (not number)

### ConfigMap / Secret
- Never hardcode secrets in manifests
- Use `stringData` for readability in Secrets
- Mount as volumes or env vars depending on update behavior needs

## Security Best Practices

- Enable `NetworkPolicy` to restrict pod-to-pod traffic
- Use `ServiceAccount` per application (not default)
- Set `automountServiceAccountToken: false` when not needed
- Use `PodSecurityStandards` (restricted profile)
- Image pull from private registry with `imagePullSecrets`

## Scaling

- `HorizontalPodAutoscaler` with CPU and memory metrics
- Set `minReplicas` >= 2 for production
- Consider `PodTopologySpreadConstraints` for zone distribution
- Use `PriorityClass` for critical workloads

## Manifest Template

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: APP_NAME
  labels:
    app: APP_NAME
spec:
  replicas: 2
  selector:
    matchLabels:
      app: APP_NAME
  template:
    metadata:
      labels:
        app: APP_NAME
    spec:
      securityContext:
        runAsNonRoot: true
      containers:
        - name: APP_NAME
          image: REGISTRY/APP_NAME:TAG
          ports:
            - containerPort: 8080
              name: http
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 512Mi
          readinessProbe:
            httpGet:
              path: /healthz
              port: http
            initialDelaySeconds: 5
          livenessProbe:
            httpGet:
              path: /healthz
              port: http
            initialDelaySeconds: 15
          securityContext:
            readOnlyRootFilesystem: true
            allowPrivilegeEscalation: false
```

When generating manifests, always ask:
1. What environment (dev/staging/prod)?
2. What traffic pattern (internal/external)?
3. What scaling requirements?
4. What security constraints?
