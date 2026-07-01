# Security Policy

## Supported Versions

We actively support and patch security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| v1.3.x  | :white_check_mark: |
| v1.2.x  | :white_check_mark: |
| < v1.2  | :x:                |

## Reporting a Vulnerability

We take the security of BullyGuard ID very seriously. If you find a security vulnerability, please do **not** report it via GitHub Issues. Instead, follow these steps:

1. Send an email to `security@bullyguard.id` describing the vulnerability.
2. Include details of the affected component (Backend, Frontend, Scraper, Database).
3. Provide step-by-step instructions or a Proof of Concept (PoC) script to reproduce the issue.

We will acknowledge your report within **24 hours** and provide a timeline for triage and remediation.

## Our Security Commitments

* **Credential Protection**: We do not store unencrypted API keys or third-party cookies in the repository.
* **Database Encryption**: All classification memory contains personal identifiable information (PII) like social media usernames, which is encrypted at rest in PostgreSQL.
* **SSRF Prevention**: All outbound webhooks must pass validation to prevent Server-Side Request Forgery.
