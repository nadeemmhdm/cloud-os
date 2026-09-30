# Architecture

Cloud Os is a Python/FastAPI personal cloud server designed for Windows and Linux.

## Core layers
- **CLI** — setup, startup, status, diagnostics.
- **Web/API** — dashboard and authenticated management endpoints.
- **Authentication** — password hashing, sessions, identities.
- **Authorization** — team/member RBAC and permission checks.
- **Storage** — restricted storage root and validated paths.
- **Terminal** — privileged server command execution for authorized roles.
- **Operations** — backups, audit records, health diagnostics.
- **Integrations** — SSH and Cloudflare Tunnel detection/startup hooks.
- **Platform startup** — OS-managed boot startup and process recovery.

## Security model
The HTTP application should run with the minimum OS privileges required. Authorization is enforced separately from authentication. Storage paths must resolve inside the configured root. Privileged actions should be logged.

The browser terminal is a high-trust capability because commands inherit the Cloud Os process privileges.
