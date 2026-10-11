# Security Architecture

- AES-256-GCM authenticated encryption for user BYOK API keys.
- Bcrypt password hashing.
- Path traversal sanitization on all video uploads and downloads.
- Tenant isolation enforced by user-specific directory structure and database checks.
