---
name: compliance-check
description: Regulatory compliance checking for GDPR, HIPAA, SOC2, PCI-DSS, CCPA. Use when auditing code for data privacy, security controls, or regulatory requirements.
---

# Compliance Check

Audit code and infrastructure for regulatory compliance.

## GDPR (General Data Protection Regulation)

### Data Collection & Processing
- [ ] Explicit user consent collected before processing personal data
- [ ] Privacy policy accessible and up-to-date
- [ ] Data processing purposes clearly defined and limited
- [ ] Legal basis documented for each data processing activity

### Data Subject Rights
- [ ] Right to access: Users can export their data
- [ ] Right to erasure: Users can delete their account and data
- [ ] Right to rectification: Users can correct their data
- [ ] Right to portability: Data exportable in machine-readable format
- [ ] Right to restrict processing: Users can opt-out of processing

### Technical Measures
- [ ] Personal data encrypted at rest and in transit
- [ ] Data minimization: Only necessary data collected
- [ ] Data retention policies implemented with automatic deletion
- [ ] Audit logs for data access and modifications
- [ ] Data processing agreements with third-party processors

## HIPAA (Health Insurance Portability and Accountability Act)

- [ ] PHI (Protected Health Information) encrypted at rest (AES-256)
- [ ] PHI encrypted in transit (TLS 1.2+)
- [ ] Access controls with unique user identification
- [ ] Audit trails for all PHI access
- [ ] Automatic session timeout
- [ ] Business Associate Agreements with vendors
- [ ] Emergency access procedures documented
- [ ] Backup and disaster recovery for PHI systems

## SOC 2

### Security
- [ ] Access control policies enforced
- [ ] Multi-factor authentication for production systems
- [ ] Network security (firewalls, segmentation)
- [ ] Vulnerability management and patching
- [ ] Incident response procedures

### Availability
- [ ] SLAs defined and monitored
- [ ] Disaster recovery plan tested
- [ ] Capacity planning documented

### Confidentiality
- [ ] Data classification scheme
- [ ] Encryption standards enforced
- [ ] Secure data disposal procedures

## PCI-DSS (Payment Card Industry)

- [ ] Cardholder data never stored in plaintext
- [ ] PAN (Primary Account Number) masked in display (show last 4 only)
- [ ] No sensitive auth data stored post-authorization
- [ ] TLS 1.2+ for all cardholder data transmission
- [ ] Strong access control measures
- [ ] Regular security testing (vulnerability scans, penetration tests)
- [ ] Network segmentation for cardholder data environment

## Code Audit Checklist

When scanning code, flag:
1. **Logging**: Personal data or secrets in log output
2. **Error messages**: PII or sensitive data in error responses
3. **Storage**: Unencrypted sensitive data in databases or files
4. **Transmission**: HTTP (non-TLS) for sensitive data
5. **Third parties**: Data shared without processing agreements
6. **Retention**: No expiration or cleanup for personal data
7. **Access**: Missing authentication or authorization checks
8. **Audit**: No logging of data access events
