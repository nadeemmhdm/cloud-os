# Cloud OS

**A lightweight, self-hosted personal cloud management layer for Windows and Linux.**

Cloud OS turns an existing computer into a privately managed server without replacing the host operating system. It provides a responsive web dashboard for storage, system monitoring, users and teams, backups, diagnostics, terminal access, integrations, and optional AI-assisted troubleshooting.

> **Development status:** Cloud OS is actively developed. Do not expose its development HTTP service directly to the public Internet.

## Website & Demo

- **Website:** https://cloud-os.qezvo.in/
- **Documentation:** https://cloud-os.qezvo.in/docs.html
- **Searchable Error Codes:** https://cloud-os.qezvo.in/errors.html
- **Product Demo:** https://cloud-os.qezvo.in/#demo

The product demo source is stored at `site/assets/cloud-os-demo.mov`.

## Highlights

- Responsive Cloud OS dashboard for desktop and mobile
- CPU, memory, storage and uptime monitoring
- Restricted Cloud OS storage root and file-management APIs
- Owner, Admin, Operator, Member and Viewer RBAC
- Users, teams and permission-aware management operations
- Host-native PowerShell on Windows and Bash on Linux
- Explicit terminal timeout, output and authorization boundaries
- Verified full Cloud OS backups with restore safety snapshots, integrity checks and protected latest backup\n- Persistent progressive login cooldowns for web and SSH authentication\n- Audit logging
- SSH and Cloudflare Tunnel integration/status hooks
- `cloud-os doctor` diagnostics
- Optional AI Help using Gemini, OpenAI, Claude or Ollama Cloud
- Documentation-grounded AI troubleshooting context
- Safe process-priority performance booster
- Windows and Linux CI security test matrix

## Install

Review installation scripts before executing remote code.

### Windows 10/11

Run PowerShell as Administrator:

```powershell
irm https://raw.githubusercontent.com/nadeemmhdm/cloud-os/main/install.ps1 | iex
```

### Linux

```bash
curl -fsSL https://raw.githubusercontent.com/nadeemmhdm/cloud-os/main/install.sh | bash
```

Then configure and start Cloud OS:

```text
cloud-os setup
cloud-os start
cloud-os status
cloud-os doctor
```

See [Installation](docs/INSTALLATION.md) for platform behavior and limitations.

## Architecture

Cloud OS runs on top of the existing host operating system. It does **not** format the machine or replace Windows/Linux.

```text
Browser / Phone / Laptop
          |
     HTTPS / Tunnel
          |
      Cloud OS API
          |
 Authentication + RBAC
          |
  ---------------------
  | Files | Terminal |
  | Backup| Audit    |
  | AI    | System   |
  ---------------------
          |
   Windows / Linux host
```

For Internet-facing access, place Cloud OS behind authenticated HTTPS/TLS access such as a properly configured tunnel, VPN, or hardened reverse proxy. A tunnel does not replace Cloud OS authentication or RBAC.

## Access Control

The built-in `admin` account is the **Owner** and retains full platform access.

| Role | Intended access |
| --- | --- |
| Owner | Full platform access; reserved for the built-in primary administrator |
| Admin | Files, terminal, backups, network, audit, teams and settings |
| Operator | Files, terminal, backups and network |
| Member | File read/write |
| Viewer | File read only |

See [Teams and RBAC](docs/TEAMS.md).

## AI Help

Cloud OS can use one configured provider: **Gemini, OpenAI, Claude, or Ollama Cloud**. Provider credentials remain server-side and must never be committed.

AI Help retrieves relevant local project documentation and supplies it as reference context for troubleshooting. This is contextual retrieval, **not model training or fine-tuning**.

## Security

Cloud OS uses salted password hashing, expiring sessions, persistent progressive login throttling for web/SSH authentication, permission checks, restricted storage paths, bounded terminal execution, audit logging, and browser same-origin checks for state-changing authenticated operations.

The web terminal executes with the operating-system privileges available to the Cloud OS process. Windows UAC is not bypassed. Grant terminal access only to trusted users.

For deployment requirements and vulnerability reporting, read [Security Policy](SECURITY.md) and [Security Architecture](docs/SECURITY.md).

## Documentation

| Guide | Purpose |
| --- | --- |
| [Installation](docs/INSTALLATION.md) | Install and platform behavior |
| [Architecture](docs/ARCHITECTURE.md) | Components and trust boundaries |
| [Security Architecture](docs/SECURITY.md) | Security model and deployment guidance |
| [Teams & RBAC](docs/TEAMS.md) | Users, roles and permissions |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Diagnosis and recovery |
| [Error Codes](docs/ERROR_CODES.md) | Stable error-code reference |
| [Updates & Rollback](docs/UPDATES.md) | Update channels and rollback |
| [Roadmap](docs/ROADMAP.md) | Planned development |
| [Contributing](CONTRIBUTING.md) | Development and pull-request standards |
| [Support](SUPPORT.md) | Bug-reporting guidance |
| [Code of Conduct](CODE_OF_CONDUCT.md) | Community expectations |
| [Changelog](CHANGELOG.md) | Project history |

## Current Limitations

Cloud OS is not yet a production-hardened appliance. In particular, signed/checksummed update artifacts, encrypted/off-device backup packaging, persistent distributed sessions, hardened Windows secret ACL handling, and full pre-login Windows service architecture remain development areas.

Current Windows automatic startup is logon-triggered. The Linux development installer does not enable Cloud OS as a root system service.

## Updates & Uninstall\n\n`cloud-os update` now uses visible real-stage progress: update check, repository fetch, source preparation, package installation and verification. It refuses to overwrite a dirty source checkout and attempts rollback if installation fails. On success it reports the installed version and Git revision.\n\n`cloud-os uninstall` asks for confirmation and preserves Cloud OS state, backups and configured storage by default. `cloud-os uninstall --purge-data` permanently removes those data locations and should be used only intentionally.\n\n## Development

Use Python 3.10 or newer.

```bash
python -m venv .venv
# activate the environment for your shell
python -m pip install -e ".[test]"
pytest -q
```

Security-sensitive changes should include regression tests and preserve Windows/Linux behavior.

## License

Cloud OS is licensed under the [MIT License](LICENSE).
