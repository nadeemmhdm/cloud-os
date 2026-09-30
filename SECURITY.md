# Security Policy

## Supported status
Cloud Os is under active development. The current development branch is not yet production-hardened for direct public Internet exposure.

## Reporting a vulnerability
Do not publish exploitable security issues, credentials, private keys, tunnel tokens, or sensitive logs in a public issue. Contact the repository maintainer privately through an appropriate GitHub security-reporting channel when available.

Include the affected version, operating system, reproduction steps, impact, and a minimal proof of concept.

## Deployment guidance
- Prefer an authenticated Cloudflare Tunnel, VPN, or hardened HTTPS reverse proxy.
- Use strong unique administrator and member passwords.
- Prefer SSH public-key authentication.
- Restrict terminal permission to trusted operators.
- Keep Cloud Os and the host operating system updated.
- Back up data before upgrades.
- Never commit secrets to this repository.

## Security boundaries
File APIs are restricted to the configured Cloud Os storage root. Team access is permission based. The web terminal executes commands with the operating-system privileges of the Cloud Os process and must therefore be treated as privileged access.
