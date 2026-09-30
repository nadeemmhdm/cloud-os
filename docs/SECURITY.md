# Security Architecture

Cloud Os uses separate authentication and authorization controls. Passwords are stored as salted PBKDF2-derived hashes rather than plaintext. Sessions expire. Management APIs check permissions for protected capabilities.

Filesystem operations resolve paths against the configured storage root and reject paths that escape it. Terminal access is privileged and should never be granted to untrusted users.

For remote deployments, place Cloud Os behind authenticated TLS access. Cloudflare Tunnel can provide transport without opening an inbound router port, but Cloud Os authentication and least-privilege roles remain necessary.

Future hardening includes persistent server-side session storage, CSRF protection review, secure-cookie enforcement behind HTTPS, rate limiting, stronger update verification, and comprehensive adversarial tests.
