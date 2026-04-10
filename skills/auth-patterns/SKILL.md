---
name: auth-patterns
description: Authentication and authorization patterns including JWT, OAuth2, RBAC, ABAC, session management, and MFA. Use when implementing login systems, access control, or security middleware.
---

# Authentication & Authorization Patterns

Implement secure auth systems.

## Authentication Methods

### JWT (JSON Web Tokens)
```typescript
// Access token: short-lived (15 min)
const accessToken = jwt.sign(
  { sub: user.id, role: user.role },
  process.env.JWT_SECRET,
  { expiresIn: '15m' }
);

// Refresh token: long-lived (7 days), stored securely
const refreshToken = jwt.sign(
  { sub: user.id, tokenVersion: user.tokenVersion },
  process.env.REFRESH_SECRET,
  { expiresIn: '7d' }
);
```

**Best Practices**:
- Short-lived access tokens (15 min max)
- Refresh tokens stored in httpOnly cookies (not localStorage)
- Include minimal claims (user ID, role — not PII)
- Implement token rotation on refresh
- Maintain a token blocklist for logout

### Session-Based
- Store session ID in httpOnly, Secure, SameSite cookie
- Server-side session store (Redis for distributed systems)
- Regenerate session ID after authentication
- Set appropriate session timeout

### OAuth 2.0 / OIDC
- Use Authorization Code flow with PKCE (not implicit)
- Validate ID token signature and claims
- Store tokens server-side when possible
- Implement proper state parameter for CSRF prevention

## Authorization Models

### RBAC (Role-Based Access Control)
```typescript
const permissions = {
  admin: ['read', 'write', 'delete', 'manage-users'],
  editor: ['read', 'write'],
  viewer: ['read'],
};

function authorize(user, permission) {
  return permissions[user.role]?.includes(permission);
}
```

### ABAC (Attribute-Based Access Control)
```typescript
function canEdit(user, resource) {
  return (
    user.role === 'admin' ||
    resource.ownerId === user.id ||
    resource.teamId === user.teamId && user.role === 'editor'
  );
}
```

## Security Checklist

- [ ] Passwords hashed with bcrypt/argon2 (not MD5/SHA)
- [ ] Rate limiting on login endpoint (prevent brute force)
- [ ] Account lockout after N failed attempts
- [ ] HTTPS only (HSTS header)
- [ ] CSRF protection on state-changing endpoints
- [ ] Secure password reset flow (time-limited tokens)
- [ ] MFA option available
- [ ] Login/logout events logged for audit
- [ ] No user enumeration (same response for valid/invalid email)
- [ ] Session invalidation on password change

## Common Vulnerabilities

| Vulnerability | Prevention |
|---|---|
| Credential stuffing | Rate limiting, MFA, breach detection |
| Session fixation | Regenerate session after login |
| Token theft | HttpOnly cookies, short expiry |
| Privilege escalation | Check permissions on every request |
| JWT confusion | Validate algorithm, use asymmetric keys |
