---
name: cloud-cost-optimize
description: Cloud infrastructure cost optimization. Use when analyzing cloud spending, right-sizing resources, identifying waste, or optimizing AWS/GCP/Azure costs.
---

# Cloud Cost Optimization

Analyze and reduce cloud infrastructure costs without sacrificing reliability.

## 1. Resource Right-Sizing

### Compute
- Check CPU utilization — if consistently < 40%, downsize the instance
- Check memory utilization — over-provisioned memory is common waste
- Use burstable instances (T-series on AWS) for variable workloads
- Consider ARM-based instances (Graviton/Ampere) for 20-40% savings
- Use spot/preemptible instances for fault-tolerant workloads

### Database
- Review RDS/Cloud SQL instance sizes vs actual usage
- Consider Aurora Serverless v2 for variable database workloads
- Check for idle read replicas
- Review provisioned IOPS vs actual usage
- Consider DynamoDB on-demand for unpredictable traffic

### Storage
- Implement S3/GCS lifecycle policies (transition to IA/Archive)
- Delete unused EBS volumes and snapshots
- Check for orphaned resources after teardowns
- Use intelligent tiering for unpredictable access patterns

## 2. Architecture Patterns

### Serverless Where Appropriate
- Lambda/Cloud Functions for event-driven workloads
- API Gateway + Lambda vs always-on servers for low-traffic APIs
- Step Functions for orchestration instead of always-on workers

### Caching
- CloudFront/CDN for static assets (reduce origin requests)
- ElastiCache/Memorystore for database query caching
- Application-level caching to reduce API calls

### Auto-Scaling
- Configure based on actual traffic patterns
- Set appropriate min/max bounds
- Use scheduled scaling for predictable patterns
- Scale down aggressively in non-production environments

## 3. Quick Wins

- [ ] Shut down non-production environments outside business hours
- [ ] Delete unattached EBS volumes, unused Elastic IPs
- [ ] Review and consolidate underutilized load balancers
- [ ] Use reserved instances or savings plans for steady-state workloads
- [ ] Enable S3 intelligent tiering
- [ ] Review data transfer costs (inter-region, NAT gateway)
- [ ] Consolidate AWS accounts under Organizations for volume discounts
- [ ] Check for idle NAT Gateways ($32/month each)

## 4. Cost Monitoring

- Set up billing alerts at 50%, 80%, 100% of budget
- Tag all resources for cost allocation
- Review Cost Explorer weekly for anomalies
- Use AWS Trusted Advisor / GCP Recommender for automated suggestions

## Report Format

```
## Cost Optimization Report
**Current Monthly Spend**: $X
**Projected Savings**: $Y (Z%)

### Immediate Savings (no risk)
| Resource | Current | Recommended | Monthly Savings |
|----------|---------|-------------|-----------------|

### Medium-Term Optimizations
| Change | Effort | Savings | Risk |
|--------|--------|---------|------|

### Architecture Changes (high impact)
| Change | Description | Estimated Savings |
|--------|-------------|-------------------|
```
