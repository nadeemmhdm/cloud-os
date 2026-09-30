# Cloud Os

**Cloud Os** turns a Windows 10/11 or Linux computer into a lightweight self-hosted personal cloud server with an animated macOS-inspired dashboard and persistent boot startup.

> Development version **v0.2.0**. Internet-facing deployments still require HTTPS/access-control hardening.

## Fast install

### Windows 10 / 11 — PowerShell (Administrator)
```powershell
irm https://raw.githubusercontent.com/nadeemmhdm/cloud-os/main/install.ps1 | iex
```

### Linux
```bash
curl -fsSL https://raw.githubusercontent.com/nadeemmhdm/cloud-os/main/install.sh | bash
```

Configuration is saved after first setup. Normal shutdown/reboot does not require setup again.

## Boot flow
```text
Computer ON → OS boots → Cloud Os starts → saved config loads
            → integrations restore → dashboard online
```

## CLI
```bash
cloud-os setup
cloud-os start
cloud-os status
```

## Current modules
- FastAPI server + health endpoint
- Animated responsive macOS-inspired dashboard
- Live CPU, RAM, storage and uptime
- Persistent configuration
- SSH startup integration
- Cloudflare Tunnel startup hook
- Windows/Linux installers
- Linux systemd restart policy
- Cross-platform CLI

## Security
Do not directly expose the development HTTP server to the Internet. Prefer an authenticated Cloudflare Tunnel, VPN, or hardened HTTPS reverse proxy. Never commit tokens, passwords, tunnel credentials, or SSH private keys. See [SECURITY.md](SECURITY.md).

## Documentation
See [docs/INSTALLATION.md](docs/INSTALLATION.md) and the `docs/` directory.

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md) and [COLLABORATE.md](COLLABORATE.md).

## License
MIT. See [LICENSE](LICENSE).
