# Installation

## Requirements
- Windows 10/11 or a supported Linux distribution
- Python 3.10+
- Git
- Administrator/root privileges for system-service installation

## Windows
Open PowerShell as Administrator:

```powershell
irm https://raw.githubusercontent.com/nadeemmhdm/cloud-os/main/install.ps1 | iex
```

## Linux
```bash
curl -fsSL https://raw.githubusercontent.com/nadeemmhdm/cloud-os/main/install.sh | bash
```

Cloud Os stores persistent configuration under its application data directory. Normal shutdown and reboot should not require repeating application configuration.

> The installers and platform autostart flow are still being hardened and require end-to-end validation before production use.

## Manual development run
```bash
git clone https://github.com/nadeemmhdm/cloud-os.git
cd cloud-os
python -m venv .venv
pip install -e .
cloud-os setup
cloud-os start
```

Run `cloud-os doctor` for diagnostics.
