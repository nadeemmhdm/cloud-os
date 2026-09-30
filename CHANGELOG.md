# Changelog

All notable Cloud Os changes are documented here.

## Unreleased
### Added
- Team and member RBAC model.
- Owner, admin, operator, member, and viewer roles.
- Team membership management APIs.
- Persistent storage root and path isolation.
- Admin/member sessions and password hashing.
- Authenticated file-management APIs.
- Admin-authorized terminal backend with timeout/output limits.
- Audit logging, backups, diagnostics, and integration status.
- Animated system dashboard foundation.
- Windows/Linux installer foundations and Linux systemd unit.

### Security
- Permission checks for files, terminal, backups, network, audit, and team management.
- Filesystem traversal protection.

### Known development work
- Complete dashboard UI for all management APIs.
- End-to-end Windows/Linux installer and autostart verification.
- Production-grade HTTPS/access deployment guidance and integration tests.
- Safe update/rollback implementation.
