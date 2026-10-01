# Changelog

All notable Cloud OS changes are documented here. Detailed release-note drafts are stored under `releases/`.

## Unreleased

## 0.2.2
### Added
- Cloud OS SSH gateway now provides role-gated native server shell access using PowerShell on Windows and Bash on Linux.
- Dashboard terminal sessions preserve the working directory between commands.
- Cloud OS AI widget supports general chat, coding and troubleshooting with automatic configured-provider selection.

### Changed
- AI provider selection was removed from the chat widget; provider configuration remains under Settings for authorized administrators.
- SSH and terminal access continue to follow Cloud OS RBAC permissions.

### Fixed
- Terminal session and SSH gateway regressions found by the Windows/Linux CI matrix.
- AI error catalog and automatic provider-selection failures.

### Added
- Standalone Cloud OS website with landing, documentation and searchable error-code pages.
- Product demo video and unified Cloud OS visual branding across the website and dashboard.
- Optional multi-provider AI Help and process-priority performance booster controls.
- Mobile hamburger navigation and responsive website improvements.

### Security
- Corrupt configuration now fails closed instead of silently falling back to defaults.
- State-changing authenticated browser requests enforce same-origin checks.
- Terminal audit records no longer store raw command text.
- AI provider HTTP failures are sanitized before reaching clients.
- Access-control database corruption fails closed instead of silently returning an empty database.
- Audit records are length-bounded, POSIX-protected and size-rotated.
- Backup names include a random suffix to prevent same-second collisions.
- Terminal timeout and authorization failures are handled explicitly.

### Fixed
- Installation documentation now matches current Windows logon-triggered startup behavior.
- Linux installer messaging no longer implies a production system service is enabled.

## 0.2.0
- Team/member RBAC and Owner/Admin/Operator/Member/Viewer roles.
- Host-native PowerShell/Bash terminal and role-aware privileged requests.
- Stronger password hashing, login throttling, storage isolation and upload limits.
- Audit, backup, diagnostics and integration improvements.
- Windows/Linux security CI matrix.

See [releases/0.2.0.md](releases/0.2.0.md).

## 0.1.0
- Initial FastAPI server, dashboard foundation, configuration, storage/file APIs, authentication, diagnostics, backup and installer foundations.

See [releases/0.1.0.md](releases/0.1.0.md).
