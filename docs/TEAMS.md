# Teams and Access Control

Cloud Os supports team-based role-based access control (RBAC).

| Role | Intended access |
| --- | --- |
| Owner | Full platform access |
| Admin | Files, terminal, backups, network, audit, teams and settings |
| Operator | Files, terminal, backups and network |
| Member | File read/write |
| Viewer | File read only |

## Permissions
Current permission keys include `files.read`, `files.write`, `terminal`, `backups`, `network`, `audit`, `teams.manage`, and `settings`.

A member can belong to multiple teams. Effective permissions are the union of the member's base role and assigned team roles.

The built-in administrator is the owner identity. Terminal access should only be granted to trusted administrators/operators.
