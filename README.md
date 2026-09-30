# Cloud Os

Cloud Os is a lightweight, self-hosted personal cloud server for Windows 10/11 and Linux, built with Python and FastAPI.

> **v0.1.0 foundation:** early development release. It is not yet a production-hardened public cloud platform.

## Features

- macOS-inspired responsive dashboard
- Administrator authentication with hashed passwords
- Restricted-root file manager
- Upload, download, folder creation and deletion
- CPU, RAM, disk and uptime monitoring
- Cross-platform CLI
- GitHub Releases update checker
- Windows + Linux CI
- Version-tag driven GitHub Release workflow
- Security, collaboration and full docs structure

## Quick start

```bash
git clone https://github.com/nadeemmhdm/cloud-os.git
cd cloud-os
python -m venv .venv
```

Windows:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -e .
cloud-os setup
cloud-os start
```

Linux:

```bash
source .venv/bin/activate
pip install -e .
cloud-os setup
cloud-os start
```

## Commands

```text
cloud-os setup
cloud-os start
cloud-os status
cloud-os update
```

## Security

Do not expose the development server directly to the public Internet. Put public deployments behind a trusted HTTPS reverse proxy, VPN, or authenticated tunnel. Read [SECURITY.md](SECURITY.md) and [docs/security.md](docs/security.md).

## Updates and releases

Cloud Os can query GitHub Releases for newer versions. Applying an update is an explicit administrator action. Release automation is version-tag driven so ordinary commits do not silently become production releases.

## Documentation

Installation, architecture, security, updates and roadmap documentation live in `docs/`.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) and [COLLABORATE.md](COLLABORATE.md).

## License

MIT License. See [LICENSE](LICENSE).
