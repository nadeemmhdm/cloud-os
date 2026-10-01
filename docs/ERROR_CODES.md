# Cloud OS Error Codes

Cloud OS uses stable error codes so users can identify a problem without reading a Python traceback. API errors use this shape:

```json
{
  "detail": {
    "error": {
      "code": "TERM-002",
      "message": "Command timed out.",
      "suggestion": "Check the command and try again."
    }
  }
}
```

The optional `detail` value contains bounded diagnostic context and should not be treated as a stable API contract.

## Authentication and authorization

| Code | Meaning | What to do |
| --- | --- | --- |
| `AUTH-001` | Invalid username or password | Verify the credentials and retry. |
| `AUTH-002` | Too many login attempts | Wait a few minutes before retrying. |
| `AUTH-003` | Login required or session expired | Sign in again. |
| `PERM-001` | Permission denied | Ask an Owner/Admin for the required role or permission. |

## Files and storage

| Code | Meaning | What to do |
| --- | --- | --- |
| `FILE-001` | File/folder not found | Refresh the listing and verify the path. |
| `FILE-002` | Invalid/unsafe path | Use a path inside the Cloud OS storage root. |
| `FILE-003` | Upload exceeds 1 GiB | Upload a smaller file or split it. |
| `FILE-004` | Storage-root deletion blocked | Delete only content inside the root. |
| `FILE-005` | Filesystem operation failed | Check disk space and host filesystem permissions. |

## Terminal

| Code | Meaning | What to do |
| --- | --- | --- |
| `TERM-001` | Invalid/unavailable shell or command | Use a shell returned by the terminal-shells endpoint and a valid command. |
| `TERM-002` | Command timed out | Check the command and retry. |
| `TERM-003` | Privileged terminal not authorized | Use Owner/Admin and satisfy Windows/Linux host authorization. |

## Users, teams and data

| Code | Meaning | What to do |
| --- | --- | --- |
| `USER-001` | User operation failed | Check username, password strength and role. |
| `TEAM-001` | Team operation failed | Check team/user names and role. |
| `DB-001` | Access database corrupt/unreadable | Restore `access.json` from a trusted backup or repair it locally. |
| `BACKUP-001` | Backup failed | Check disk space and data-directory permissions. |
| `SYS-001` | Internal Cloud OS error | Run `cloud-os doctor` and inspect server/audit logs. |

## CLI / installer and updater codes

The CLI already emits codes including:

| Code | Meaning |
| --- | --- |
| `C001` | Required command is missing |
| `C002` | External command failed |
| `S001` | Initial setup/password validation failed |
| `SVC00` | System service installation intentionally unavailable |
| `U001` | Git is missing |
| `U002` | Cloud OS source checkout not found |
| `U003` | Latest release tag missing |
| `U004` | Invalid update source |
| `U404` | No GitHub Release published |
| `UHTTP` | GitHub returned an HTTP error |
| `UNET` | GitHub/network connection failed |

## Support rule

When reporting a problem, include the error code, Cloud OS version, host OS and the output of `cloud-os doctor`. Do not share passwords, session cookies, tunnel tokens, private keys or other secrets.
