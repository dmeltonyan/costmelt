# Cost Melt - Security Documentation

Complete security architecture, threat model, and best practices for Cost Melt authentication and authorization.

---

## Table of Contents

- [Overview](#overview)
- [Components](#components)
- [Architecture](#architecture)
- [Threat Model](#threat-model)
- [Best Practices](#best-practices)
- [Admin Workflow](#admin-workflow)
- [API Key Management](#api-key-management)

---

## Overview

Cost Melt implements a production-grade authentication and authorization system to protect API endpoints, prevent abuse, and ensure secure access to LLM routing services.

### Why Security Matters

Cost Melt handles:
- **Sensitive API keys** for multiple LLM providers (OpenAI, Anthropic, etc.)
- **Cost optimization** that can significantly impact billing
- **User data** and request logs
- **Rate-limited resources** that can be abused

Without proper security, attackers could:
- Steal API keys and rack up charges
- Abuse the system to cause service degradation
- Access sensitive user data
- Bypass rate limits and cost controls

### Security Principles

1. **Never store plaintext API keys** - All keys are bcrypt hashed
2. **Least privilege** - Role-based access control (RBAC)
3. **Rate limiting** - Prevent abuse and DoS attacks
4. **Audit logging** - Track all authentication events
5. **Defense in depth** - Multiple layers of security

---

## Components

### 1. API Key Manager (`backend/security/api_key_manager.py`)

**Purpose:** Manages the complete lifecycle of API keys.

**Features:**
- **Secure key generation** - Cryptographically secure random keys (48+ bytes)
- **bcrypt hashing** - Cost factor 12 (production-grade)
- **Prefix-based lookup** - First 8 characters for fast database queries
- **Expiration support** - Optional time-based expiration
- **Role assignment** - admin, write, or read permissions
- **Usage tracking** - Last used timestamp

**Key Format:**
```
cm_live_<48-character-base64>
```

**Security Features:**
- Keys are hashed with bcrypt before storage
- Plaintext keys are shown only once during creation
- Prefix allows fast database lookup without full hash comparison
- Expired keys are automatically rejected

### 2. Authentication Middleware (`backend/middleware/auth_middleware.py`)

**Purpose:** Validates API keys on all protected routes.

**Behavior:**
- Intercepts all requests to `/v1/*`, `/dashboard/*`, and `/auth/*`
- Extracts API key from:
  - `Authorization: Bearer <key>` header
  - `x-api-key: <key>` header
- Verifies key using APIKeyManager
- Attaches user info to `request.state`:
  - `user_id`
  - `project_id`
  - `role`
  - `key_id`

**Public Endpoints (No Auth Required):**
- `/health`
- `/docs`
- `/openapi.json`
- `/redoc`

**Error Responses:**
- `401 Unauthorized` - Missing or invalid API key
- `403 Forbidden` - Insufficient permissions (handled by RBAC)

### 3. Role-Based Access Control (`backend/security/rbac.py`)

**Purpose:** Enforce role-based permissions on endpoints.

**Roles:**

| Role | Permissions | Use Case |
|------|-------------|----------|
| **read** | View metrics only (`GET /dashboard/*`) | Analytics dashboards, monitoring |
| **write** | Call `/v1/route` + view metrics | Application integration |
| **admin** | Full access including API key management | Service administrators |

**Usage:**
```python
@router.get("/dashboard/stats")
@require_role("read")
async def get_stats(request: Request):
    # Only read, write, or admin can access
    ...

@router.post("/auth/api-keys")
@require_role("admin")
async def create_api_key(request: Request):
    # Only admin can create API keys
    ...
```

**Role Hierarchy:**
- `read` < `write` < `admin`
- Higher roles inherit lower role permissions

### 4. Rate Limiting Middleware (`backend/middleware/rate_limit.py`)

**Purpose:** Prevent abuse and DoS attacks using token bucket algorithm.

**Algorithm:**
- **Token Bucket** - Each user has a bucket of tokens
- **Refill Rate** - Tokens refill every 60 seconds
- **Default Limit** - 60 requests/minute per user
- **Pro Limit** - 600 requests/minute
- **Enterprise** - Custom limits per project

**Redis Implementation:**
- Key: `ratelimit:{user_id}`
- Value: Current token count
- TTL: 60 seconds (auto-refill)

**Response Headers:**
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 27
X-RateLimit-Reset: 1704067200
Retry-After: 42
```

**Error Response:**
```json
{
  "error": "Rate limit exceeded",
  "code": 429,
  "message": "Too many requests. Limit: 60 per 60 seconds",
  "retry_after": 42,
  "limit": 60,
  "remaining": 0
}
```

**Fail-Open Behavior:**
- If Redis is unavailable, requests are allowed (availability over strict rate limiting)
- Errors are logged for monitoring

### 5. Authentication API (`backend/api/auth.py`)

**Endpoints:**

| Endpoint | Method | Role | Description |
|----------|--------|------|-------------|
| `/auth/api-keys` | POST | admin | Create new API key |
| `/auth/api-keys` | GET | admin | List user's API keys |
| `/auth/api-keys/{key_id}` | DELETE | admin | Revoke API key |
| `/auth/api-keys/{key_id}/rotate` | POST | admin | Rotate API key |
| `/auth/me` | GET | any | Get current user info |

**Security Notes:**
- Plaintext keys are returned only during creation/rotation
- Revoked keys are soft-deleted (status = "revoked")
- All operations are logged for audit

---

## Architecture

### Request Flow

```
┌─────────────┐
│   Client    │
│  Request    │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  CORS Middleware    │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Auth Middleware    │  ← Validates API key
│  - Extract key      │
│  - Verify hash      │
│  - Check expiration │
│  - Attach user info │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Rate Limit          │  ← Token bucket check
│ Middleware          │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  RBAC Decorator     │  ← Role check
│  @require_role()    │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Route Handler      │  ← Business logic
│  /v1/route          │
└─────────────────────┘
```

### Database Schema

**api_keys Table:**
```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    key_hash TEXT NOT NULL,      -- bcrypt hash
    prefix TEXT NOT NULL,         -- First 8 chars
    role TEXT NOT NULL,            -- admin, write, read
    created_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,       -- NULL = never expires
    status TEXT,                   -- active, revoked
    metadata JSONB
);
```

**Indexes:**
- `idx_api_keys_prefix` - Fast lookup by prefix
- `idx_api_keys_user_id` - User's keys
- `idx_api_keys_user_project` - Project-specific keys
- `idx_api_keys_status` - Active keys only

### Key Verification Flow

```
1. Client sends: Authorization: Bearer cm_live_abc123...
2. Extract prefix: "abc12345"
3. Query DB: SELECT * FROM api_keys WHERE prefix = 'abc12345' AND status = 'active'
4. For each matching key:
   a. Check expiration
   b. bcrypt.compare(provided_key, stored_hash)
   c. If match: return user info
5. Update last_used_at
6. Attach to request.state
```

---

## Threat Model

### Protected Against

#### 1. Token Leakage

**Threat:** API key exposed in logs, error messages, or client-side code.

**Mitigation:**
- Keys are never logged in plaintext
- Error messages don't reveal key validity
- Keys shown only once during creation
- Revocation immediately disables keys

**Best Practice:** Rotate keys immediately if suspected compromise.

#### 2. Replay Attacks

**Threat:** Attacker intercepts valid API key and reuses it.

**Mitigation:**
- Rate limiting prevents rapid reuse
- HTTPS required in production (prevents interception)
- Keys can be revoked instantly
- Usage tracking detects anomalies

**Best Practice:** Use HTTPS only, rotate keys regularly.

#### 3. Abuse of /v1/route

**Threat:** Attacker uses API to make expensive LLM calls.

**Mitigation:**
- Rate limiting (60 req/min default)
- Role-based access (write role required)
- Cost tracking and alerts
- Per-user usage limits (future)

**Best Practice:** Set up billing alerts, monitor usage patterns.

#### 4. Abuse of Expensive Models

**Threat:** Attacker forces routing to expensive models (GPT-4o).

**Mitigation:**
- Routing engine optimizes for cost
- Complexity-based routing prevents overkill
- Cost calculator tracks savings
- Admin can set model restrictions (future)

**Best Practice:** Monitor cost per user, set budget limits.

#### 5. Brute Force Key Guessing

**Threat:** Attacker tries to guess valid API keys.

**Mitigation:**
- 48+ character keys (2^288 possible keys)
- bcrypt hashing (slow verification)
- Rate limiting on authentication
- Prefix lookup reduces database load

**Best Practice:** Use long, random keys (default is secure).

#### 6. Credential Stuffing

**Threat:** Attacker uses leaked keys from other services.

**Mitigation:**
- Unique key format (`cm_live_...`)
- Key rotation recommended
- Usage tracking detects anomalies
- Revocation for suspicious activity

**Best Practice:** Rotate keys if you suspect compromise elsewhere.

#### 7. Privilege Escalation

**Threat:** User with "read" role tries to call `/v1/route`.

**Mitigation:**
- RBAC decorators enforce role checks
- Role stored in database (can't be forged)
- Middleware validates on every request

**Best Practice:** Use least privilege principle.

#### 8. Database Compromise

**Threat:** Attacker gains access to database.

**Mitigation:**
- Keys are bcrypt hashed (can't be reversed)
- Plaintext keys never stored
- Even with hash, keys can't be extracted

**Best Practice:** Encrypt database at rest, use connection encryption.

---

## Best Practices

### 1. Never Store Plaintext API Keys

**❌ Bad:**
```python
# Storing plaintext in database
api_key = "cm_live_abc123..."
db.insert({"key": api_key})  # NEVER DO THIS
```

**✅ Good:**
```python
# Hash before storage
key_hash = bcrypt.hashpw(api_key.encode(), bcrypt.gensalt())
db.insert({"key_hash": key_hash})
```

### 2. Rotate Keys Regularly

**Recommendation:**
- **Production keys:** Rotate every 90 days
- **Development keys:** Rotate every 30 days
- **Suspected compromise:** Rotate immediately

**How to Rotate:**
```bash
# Via API
POST /auth/api-keys/{key_id}/rotate

# Returns new key (shown once)
{
  "api_key": "cm_live_new_key...",
  "key_id": "..."
}
```

### 3. Use Role Scoping

**Principle:** Grant minimum required permissions.

**Examples:**
- **Dashboard viewer:** `read` role only
- **Application integration:** `write` role
- **Service admin:** `admin` role

**Implementation:**
```python
# Read-only endpoint
@router.get("/dashboard/stats")
@require_role("read")
async def get_stats():
    ...

# Write endpoint
@router.post("/v1/route")
@require_role("write")
async def route():
    ...

# Admin endpoint
@router.post("/auth/api-keys")
@require_role("admin")
async def create_key():
    ...
```

### 4. Use HTTPS Only

**Requirement:** All API communication must use HTTPS in production.

**Why:**
- Prevents man-in-the-middle attacks
- Protects API keys in transit
- Required for secure authentication

**Configuration:**
- Railway/Render: Automatic HTTPS
- AWS: Use Application Load Balancer with ACM certificate
- Custom: Use Let's Encrypt or similar

### 5. Not Storing Per-Request Logs Without Consent

**Privacy:** Don't log full prompts/responses without user consent.

**What to Log:**
- ✅ Request metadata (user_id, model, tokens, cost)
- ✅ Error messages (sanitized)
- ✅ Authentication events
- ❌ Full prompt text (unless consented)
- ❌ Full response text (unless consented)

**Implementation:**
```python
# Log metadata only
logger.info(f"Request: user={user_id}, model={model}, tokens={tokens}")

# Don't log:
# logger.info(f"Prompt: {prompt}")  # ❌ Privacy risk
```

### 6. CORS Settings

**Production Configuration:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dashboard.costmelt.io",
        "https://costmelt.io"
    ],  # Specific domains only
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "x-api-key", "Content-Type"],
)
```

**Development:**
```python
allow_origins=["*"]  # OK for local dev only
```

### 7. Monitor and Alert

**Key Metrics:**
- Failed authentication attempts
- Rate limit violations
- Unusual usage patterns
- Cost anomalies

**Alerts:**
- Multiple failed auth attempts from same IP
- Sudden cost increase
- Rate limit exceeded repeatedly
- New API key creation

### 8. Secure Key Storage

**Client-Side:**
- Store keys in environment variables
- Never commit to version control
- Use secrets managers (AWS Secrets Manager, etc.)

**Server-Side:**
- Use platform secrets (Railway, Render, AWS Secrets Manager)
- Encrypt at rest
- Rotate regularly

---

## Admin Workflow

### Initial Setup

1. **Create First Admin Key:**
   ```bash
   # Via Supabase SQL (one-time setup)
   INSERT INTO api_keys (user_id, project_id, key_hash, prefix, role, status)
   VALUES (
     'admin-user-123',
     'default-project',
     '<bcrypt_hash>',
     '<prefix>',
     'admin',
     'active'
   );
   ```

2. **Or Use API (after first admin key exists):**
   ```bash
   curl -X POST https://api.costmelt.io/auth/api-keys \
     -H "Authorization: Bearer <admin-key>" \
     -H "Content-Type: application/json" \
     -d '{
       "project_id": "my-project",
       "role": "admin"
     }'
   ```

### Creating Keys for Users

1. **Admin creates key:**
   ```bash
   POST /auth/api-keys
   {
     "project_id": "user-project-123",
     "role": "write"
   }
   ```

2. **Response (shown once):**
   ```json
   {
     "api_key": "cm_live_abc123...",
     "prefix": "abc12345",
     "key_id": "uuid-here",
     "user_id": "user-123",
     "project_id": "user-project-123",
     "role": "write",
     "created_at": "2025-01-01T00:00:00Z"
   }
   ```

3. **Share key securely** (encrypted channel, password manager, etc.)

### Rotating Keys

1. **Rotate existing key:**
   ```bash
   POST /auth/api-keys/{key_id}/rotate
   ```

2. **Old key is revoked, new key returned**

3. **Update client applications** with new key

### Revoking Keys

1. **Revoke compromised key:**
   ```bash
   DELETE /auth/api-keys/{key_id}
   ```

2. **Key immediately becomes invalid**

3. **All requests with that key return 401**

---

## API Key Management

### Key Lifecycle

```
┌─────────────┐
│   Created   │  ← Admin creates key
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Active    │  ← Used for authentication
└──────┬──────┘
       │
       ├─────────────┐
       │             │
       ▼             ▼
┌─────────────┐  ┌─────────────┐
│  Expired    │  │   Revoked   │
└─────────────┘  └─────────────┘
```

### Key States

| State | Description | Can Authenticate? |
|-------|-------------|------------------|
| **active** | Key is valid and not expired | ✅ Yes |
| **revoked** | Key was manually disabled | ❌ No |
| **expired** | Key passed expiration date | ❌ No |

### Key Metadata

Store optional metadata with keys:
```json
{
  "environment": "production",
  "application": "mobile-app",
  "team": "backend-team",
  "notes": "Key for staging environment"
}
```

Useful for:
- Tracking key purpose
- Identifying which keys to rotate
- Audit and compliance

---

## Security Checklist

### Before Production

- [ ] All API keys use bcrypt hashing
- [ ] HTTPS enabled for all endpoints
- [ ] CORS configured for specific domains
- [ ] Rate limiting enabled (60 req/min minimum)
- [ ] RBAC implemented on all protected routes
- [ ] Audit logging enabled
- [ ] Key rotation process documented
- [ ] Secrets stored in secure manager
- [ ] Database encrypted at rest
- [ ] Connection encryption enabled
- [ ] Monitoring and alerts configured
- [ ] Incident response plan documented

### Regular Maintenance

- [ ] Rotate production keys every 90 days
- [ ] Review failed authentication logs weekly
- [ ] Monitor rate limit violations
- [ ] Review and revoke unused keys monthly
- [ ] Update dependencies for security patches
- [ ] Review and update CORS settings
- [ ] Test key rotation process quarterly

---

## Incident Response

### If API Key is Compromised

1. **Immediately revoke key:**
   ```bash
   DELETE /auth/api-keys/{compromised_key_id}
   ```

2. **Check logs for suspicious activity:**
   - Unusual request patterns
   - Requests from unknown IPs
   - Cost anomalies

3. **Rotate all related keys:**
   - Keys for same user/project
   - Keys created around same time

4. **Notify affected users**

5. **Review security controls:**
   - How was key compromised?
   - What can be improved?

### If Rate Limit is Bypassed

1. **Check Redis connectivity**
2. **Review rate limit configuration**
3. **Temporarily lower limits if needed**
4. **Investigate source of abuse**

### If Database is Compromised

1. **Rotate all API keys immediately**
2. **Review database access logs**
3. **Check for data exfiltration**
4. **Notify users of potential breach**
5. **Implement additional security measures**

---

## Compliance Considerations

### GDPR

- **Data Minimization:** Only store necessary user data
- **Right to Deletion:** Provide key revocation
- **Consent:** Get consent before logging prompts/responses

### SOC 2

- **Access Control:** RBAC and API key management
- **Audit Logging:** Track all authentication events
- **Encryption:** Keys hashed, HTTPS required

### HIPAA (if applicable)

- **Encryption:** All data in transit and at rest
- **Access Controls:** Strict RBAC
- **Audit Trails:** Complete logging

---

## Support

For security concerns:

- **Security Issues:** security@costmelt.com
- **General Support:** support@costmelt.com
- **Documentation:** [https://docs.costmelt.com/security](https://docs.costmelt.com/security)

**Last Updated:** January 2025

