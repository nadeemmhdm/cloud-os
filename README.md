# Cloud Os

Cloud Os is a lightweight self-hosted personal cloud server for Windows 10/11 and Linux. It combines a responsive management dashboard with persistent configuration, restricted storage, diagnostics, SSH/Cloudflare integration hooks, backups, an authorized server terminal, and team-based access control.

> **Development status:** Cloud Os is actively being built. Do not expose the development HTTP service directly to the public Internet.

## Fast install

### Windows 10/11
Run PowerShell as Administrator:

```powershell
irm https://raw.githubusercontent.com/nadeemmhdm/cloud-os/main/install.ps1 | iex
```

### Linux
```bash
curl -fsSL https://raw.githubusercontent.com/nadeemmhdm/cloud-os/main/install.sh | bash
```

The installer/autostart path is still undergoing end-to-end platform validation. See [Installation](docs/INSTALLATION.md) before production deployment.

## Core commands

```text
cloud-os setup
cloud-os start
cloud-os status
cloud-os doctor
```

## Implemented foundation

- FastAPI server and health/system endpoints
- Responsive animated dashboard foundation
- CPU, RAM, storage and uptime monitoring
- Persistent configuration and isolated storage root
- File listing, upload, download, folder creation and deletion APIs
- Password hashing and expiring authenticated sessions
- Team/member RBAC with Owner, Admin, Operator, Member and Viewer roles
- Permission checks for files, terminal, backups, network, audit and team management
- Authorized server terminal backend with timeout/output limits
- Audit logging
- On-demand backups
- SSH and Cloudflare Tunnel integration/status hooks
- `cloud-os doctor` diagnostics
- Linux systemd service foundation
- Windows/Linux installer foundations

## Access model

The built-in administrator is the **Owner**. Administrators can create users and teams and assign roles. Members may belong to multiple teams; effective permissions are combined from their assigned roles.

See [Teams and Access Control](docs/TEAMS.md).

## Documentation

- [Installation](docs/INSTALLATION.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Security Architecture](docs/SECURITY.md)
- [Teams and RBAC](docs/TEAMS.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Updates and Rollback](docs/UPDATES.md)
- [Roadmap](docs/ROADMAP.md)
- [Security Policy](SECURITY.md)
- [Contributing](CONTRIBUTING.md)
- [Collaboration Guide](COLLABORATE.md)
- [Support](SUPPORT.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Changelog](CHANGELOG.md)

## Security

Terminal access inherits the operating-system privileges of the Cloud Os process. Grant it only to trusted operators. Prefer SSH keys and authenticated HTTPS/tunnel access, use strong unique passwords, and never commit credentials or private keys.

See [SECURITY.md](SECURITY.md).

## Project status

Several management APIs are implemented, but the complete multi-page management UI, production-grade automatic update/rollback, and full Windows/Linux end-to-end verification remain development work. See the [Roadmap](docs/ROADMAP.md).

## License

Cloud Os is available under the [MIT License](LICENSE).
