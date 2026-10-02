# Security Architecture

Cloud Os uses separate authentication and authorization controls. Passwords are stored as salted PBKDF2-derived hashes rather than plaintext. Sessions expire. Web and SSH password authentication use persistent progressive login cooldowns to slow repeated guessing attempts. Management APIs check permissions for protected capabilities.

Filesystem operations resolve paths against the configured storage root and reject paths that escape it. Terminal access is privileged and should never be granted to untrusted users.

For remote deployments, place Cloud Os behind authenticated TLS access. Cloudflare Tunnel can provide transport without opening an inbound router port, but Cloud Os authentication and least-privilege roles remain necessary.

Updates refuse dirty source checkouts and attempt rollback after failed installation. Uninstall preserves state and storage unless destructive purge is explicitly requested. Full Cloud OS backups include integrity manifests and pre-restore safety snapshots; they are not encrypted backup archives.\n\nRemaining hardening includes persistent server-side session storage, stronger CSRF/proxy-aware origin controls, secure-cookie enforcement behind HTTPS, Windows ACL hardening, encrypted/off-device backups, signed/checksummed update artifacts, SSH key authentication, and a least-privilege pre-login Windows service architecture.
