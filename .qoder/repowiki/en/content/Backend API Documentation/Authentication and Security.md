# Authentication and Security

<cite>
**Referenced Files in This Document**
- [main.py](file://cyberbullying_api/main.py)
- [deps.py](file://cyberbullying_api/routes/deps.py)
- [auth.py](file://cyberbullying_api/routes/auth.py)
- [SECURITY_HARDENING.md](file://docs/SECURITY_HARDENING.md)
- [test_security.py](file://cyberbullying_api/tests/test_security.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Dependency Analysis](#dependency-analysis)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Conclusion](#conclusion)
10. [Appendices](#appendices)

## Introduction
This document explains the authentication and security model for the BullyGuard ID API. It covers JWT-based authentication, legacy X-API-Key support with constant-time verification, rate limiting, security middleware (headers, request size limits), environment-specific behavior, and production hardening guidance. Practical examples and best practices are included to help API consumers integrate securely.

## Project Structure
Security-related logic is implemented across the FastAPI application entrypoint and route dependencies:
- Application-wide middleware for security headers and request size limits
- Route-level dependencies for API key validation and JWT-based access control
- Tests validating rate limiting behavior and safe webhook URL checks

```mermaid
graph TB
A["main.py<br/>Application Entrypoint"] --> B["SecurityHeadersMiddleware<br/>Adds security headers"]
A --> C["RequestSizeLimitMiddleware<br/>Enforces request size limits"]
A --> D["routes/deps.py<br/>Dependencies & Security Utilities"]
D --> E["verify_api_key()<br/>X-API-Key validation"]
D --> F["get_current_user()<br/>JWT + RBAC"]
D --> G["rate_limit_cloud_llm_and_batch()<br/>Redis-backed rate limiting"]
D --> H["is_safe_webhook_url()<br/>Defensive SSRF checks"]
```

**Diagram sources**
- [main.py](file://cyberbullying_api/main.py)
- [deps.py](file://cyberbullying_api/routes/deps.py)

**Section sources**
- [main.py](file://cyberbullying_api/main.py)
- [deps.py](file://cyberbullying_api/routes/deps.py)

## Core Components
- JWT-based authentication with HS256 and scope-based RBAC
- Legacy X-API-Key header support with constant-time HMAC comparison
- Security headers middleware for standard protections
- Request size limit middleware to prevent oversized payloads
- Redis-backed rate limiting with configurable policy and fail-open/fail-closed behavior
- Defensive webhook URL validation to mitigate SSRF risks

**Section sources**
- [deps.py](file://cyberbullying_api/routes/deps.py)
- [main.py](file://cyberbullying_api/main.py)
- [SECURITY_HARDENING.md](file://docs/SECURITY_HARDENING.md)

## Architecture Overview
The security stack is layered:
- Middleware applies global protections to all responses and enforces request size limits
- Route dependencies enforce authentication and authorization policies
- Environment variables control behavior differences between development and production

```mermaid
graph TB
subgraph "Incoming Request"
U["Client"]
end
subgraph "FastAPI App"
M1["SecurityHeadersMiddleware"]
M2["RequestSizeLimitMiddleware"]
R["Route Handlers"]
D["Route Dependencies (deps.py)"]
end
subgraph "External Services"
RL["Redis (Rate Limiter)"]
LLM["Cloud LLM / Batch Jobs"]
end
U --> M1 --> M2 --> R
R --> D
D --> RL
D --> LLM
```

**Diagram sources**
- [main.py](file://cyberbullying_api/main.py)
- [deps.py](file://cyberbullying_api/routes/deps.py)

## Detailed Component Analysis

### JWT-Based Authentication and RBAC
- Token source: Authorization Bearer header
- Algorithm: HS256
- Scope validation: Route handlers declare required scopes; mismatch yields 403
- Development bypass: When enabled and both JWT and API key are absent, a dev admin principal is returned for convenience
- Failure modes: Invalid/expired tokens yield 401 with WWW-Authenticate headers

```mermaid
sequenceDiagram
participant C as "Client"
participant A as "Auth Route"
participant D as "get_current_user()"
participant T as "JWT Library"
C->>A : "Authorization : Bearer <token>"
A->>D : "Depends(oauth2_scheme)"
D->>T : "Decode and validate token"
T-->>D : "Claims + Scopes"
D->>D : "Verify required scopes"
D-->>A : "Current user + scopes"
A-->>C : "200 OK or 401/403"
```

**Diagram sources**
- [deps.py](file://cyberbullying_api/routes/deps.py)

**Section sources**
- [deps.py](file://cyberbullying_api/routes/deps.py)

### Legacy X-API-Key Authentication (Constant-Time)
- Header: X-API-Key
- Validation: Constant-time comparison using HMAC digest comparison
- Environment rules:
  - Development: Optionally bypass when a flag allows missing API key
  - Production/Staging: API key must be present and valid; otherwise 401 or server misconfiguration errors
- Backward compatibility: If no JWT but an API key is provided, a scoped principal is granted

```mermaid
flowchart TD
Start(["Entry: verify_api_key()"]) --> GetEnv["Read API_KEY from env"]
GetEnv --> CheckEmpty{"API_KEY empty?"}
CheckEmpty --> |Yes| DevMode{"Development and allowed?"}
DevMode --> |Yes| AllowDev["Allow (dev bypass)"]
DevMode --> |No| Raise500["Raise 500 (misconfiguration)"]
CheckEmpty --> |No| CheckHeader{"X-API-Key provided?"}
CheckHeader --> |No| Raise401a["Raise 401 (missing key)"]
CheckHeader --> |Yes| Compare["Constant-time compare"]
Compare --> Match{"Match?"}
Match --> |No| Raise401b["Raise 401 (invalid key)"]
Match --> |Yes| Done(["OK"])
```

**Diagram sources**
- [deps.py](file://cyberbullying_api/routes/deps.py)

**Section sources**
- [deps.py](file://cyberbullying_api/routes/deps.py)
- [SECURITY_HARDENING.md](file://docs/SECURITY_HARDENING.md)

### Security Headers Middleware
- Applied to all responses
- Standard headers include content-type options, frame options, XSS protection, referrer policy, permissions policy, cache-control
- HSTS enforced in non-development environments

```mermaid
flowchart TD
Req(["Incoming Request"]) --> Next["Call downstream handler"]
Next --> Resp["Build Response"]
Resp --> AddHdrs["Add security headers"]
AddHdrs --> HSTS{"Development?"}
HSTS --> |No| SetHSTS["Set HSTS header"]
HSTS --> |Yes| SkipHSTS["Skip HSTS"]
SetHSTS --> Out(["Return Response"])
SkipHSTS --> Out
```

**Diagram sources**
- [main.py](file://cyberbullying_api/main.py)

**Section sources**
- [main.py](file://cyberbullying_api/main.py)
- [SECURITY_HARDENING.md](file://docs/SECURITY_HARDENING.md)

### Request Size Limit Middleware
- Enforces a maximum request body size (default 10 MB)
- Returns 413 Payload Too Large when exceeded
- Validates against Content-Length header before processing body

```mermaid
flowchart TD
Enter(["Request Received"]) --> HasCL{"Has Content-Length?"}
HasCL --> |No| Proceed["Proceed (let server handle)"]
HasCL --> |Yes| Parse["Parse length"]
Parse --> Exceeds{"Exceeds max?"}
Exceeds --> |Yes| TooBig["413 Payload Too Large"]
Exceeds --> |No| Continue["Continue processing"]
```

**Diagram sources**
- [main.py](file://cyberbullying_api/main.py)

**Section sources**
- [main.py](file://cyberbullying_api/main.py)
- [SECURITY_HARDENING.md](file://docs/SECURITY_HARDENING.md)

### Rate Limiting (Redis-backed)
- Applies to expensive endpoints (e.g., hybrid prediction)
- Default policy: N requests per window per client IP and path
- Redis pipeline increments counters and sets expiry on first use
- Failure behavior:
  - Development: fail-open by default when Redis is unavailable
  - Production: fail-closed unless explicitly configured to fail-open

```mermaid
sequenceDiagram
participant C as "Client"
participant R as "Route"
participant D as "rate_limit_cloud_llm_and_batch()"
participant RC as "Redis"
C->>R : "Request"
R->>D : "Check rate limit"
D->>RC : "Pipeline incr + ttl"
RC-->>D : "Count, TTL"
alt "Count <= limit"
D-->>R : "OK"
R-->>C : "Response"
else "Count > limit"
D-->>R : "Raise 429"
R-->>C : "429 Too Many Requests"
end
```

**Diagram sources**
- [deps.py](file://cyberbullying_api/routes/deps.py)

**Section sources**
- [deps.py](file://cyberbullying_api/routes/deps.py)
- [test_security.py](file://cyberbullying_api/tests/test_security.py)
- [SECURITY_HARDENING.md](file://docs/SECURITY_HARDENING.md)

### Webhook URL Safety (SSRF Mitigation)
- Validates scheme and hostname to avoid SSRF into internal/private networks
- Production defaults to HTTPS-only unless explicitly allowed
- Optional allowlist via environment variable for controlled integrations

```mermaid
flowchart TD
Start(["URL to validate"]) --> Scheme["Check scheme (http/https)"]
Scheme --> |Invalid| Block["Block"]
Scheme --> |Valid| Host["Parse hostname"]
Host --> Private{"Private/Loopback/Link-local?"}
Private --> |Yes| Block
Private --> |No| ProdOnly{"Production?"}
ProdOnly --> |Yes| HTTPS{"HTTPS?"}
HTTPS --> |No| Block
HTTPS --> |Yes| Allow["Allow"]
ProdOnly --> |No| Allow
```

**Diagram sources**
- [deps.py](file://cyberbullying_api/routes/deps.py)

**Section sources**
- [deps.py](file://cyberbullying_api/routes/deps.py)

## Dependency Analysis
- Route handlers depend on route dependencies for authentication and rate limiting
- Security middleware is registered globally and runs before route handlers
- Redis is an optional external dependency for rate limiting; tests simulate failures and validate behavior

```mermaid
graph LR
M["main.py"] --> S["SecurityHeadersMiddleware"]
M --> Z["RequestSizeLimitMiddleware"]
M --> H["Route Handlers"]
H --> DEP["routes/deps.py"]
DEP --> RL["Redis (optional)"]
```

**Diagram sources**
- [main.py](file://cyberbullying_api/main.py)
- [deps.py](file://cyberbullying_api/routes/deps.py)

**Section sources**
- [main.py](file://cyberbullying_api/main.py)
- [deps.py](file://cyberbullying_api/routes/deps.py)

## Performance Considerations
- Constant-time comparisons eliminate timing-side-channel risks
- Redis pipeline minimizes round-trips for counter updates
- Request size limits protect memory and CPU resources from oversized payloads
- HSTS reduces TLS negotiation overhead after initial connection

## Troubleshooting Guide
Common issues and resolutions:
- 401 Unauthorized (API key)
  - Ensure the X-API-Key header matches the configured value
  - Confirm environment is not in dev bypass mode unintentionally
- 401 Unauthorized (JWT)
  - Verify the Authorization header uses Bearer token format
  - Confirm token is unexpired and signed with the correct algorithm
- 403 Forbidden (RBAC)
  - Confirm the token includes the required scopes for the endpoint
- 429 Too Many Requests
  - Reduce request frequency or adjust rate limit configuration
  - Check Redis availability; in production, a failure blocks requests by design
- 413 Payload Too Large
  - Reduce request body size or increase limits cautiously
- 500 Internal Server Error (API key misconfiguration)
  - Set API_KEY in production; development may allow bypass via configuration

**Section sources**
- [deps.py](file://cyberbullying_api/routes/deps.py)
- [test_security.py](file://cyberbullying_api/tests/test_security.py)

## Conclusion
The BullyGuard ID API employs a layered security model combining modern JWT-based authentication, legacy API key support with constant-time verification, robust middleware protections, and configurable rate limiting. Production deployments should enforce strict environment variables, disable dev bypasses, and harden network and runtime configurations to mitigate common threats.

## Appendices

### Practical Examples and Best Practices
- Authentication flow
  - Use Bearer tokens for JWT-based access; include Authorization header
  - For legacy integrations, supply X-API-Key header
  - Combine both headers only when required by your integration needs
- Proper header usage
  - Authorization: Bearer <your-jwt-token>
  - X-API-Key: <your-api-key>
- Security best practices
  - Rotate secrets regularly and store them in secure environment stores
  - Disable dev bypass flags in production
  - Monitor rate limiting violations and adjust thresholds as needed
  - Prefer HTTPS-only webhooks and maintain allowlists for outbound destinations

**Section sources**
- [deps.py](file://cyberbullying_api/routes/deps.py)
- [SECURITY_HARDENING.md](file://docs/SECURITY_HARDENING.md)