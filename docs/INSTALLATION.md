# Installation

Cloud OS includes prerequisite checks so a fresh supported machine needs as little manual setup as possible.

## Requirements handled by the installer

- Python 3.10+ (Windows installer installs Python 3.12 when needed)
- pip
- Git
- Python application dependencies from `pyproject.toml`
- Linux virtual environment
- service setup where supported

Administrator/root permission and Internet access are required during installation.

## Windows 10/11

Open PowerShell **as Administrator**:

```powershell
irm https://raw.githubusercontent.com/nadeemmhdm/cloud-os/main/install.ps1 | iex
```

The installer checks prerequisites, uses `winget` to install missing Git/Python, installs Cloud OS, runs setup and diagnostics, and prints a readable error code plus a suggested fix when a step fails.

The Windows installer registers a current-user Task Scheduler entry and starts it after setup. This is **logon-triggered**, not a pre-login Windows service. For unattended/headless production use, keep this limitation in mind.

## Linux

```bash
curl -fsSL https://raw.githubusercontent.com/nadeemmhdm/cloud-os/main/install.sh | bash
```

Debian/Ubuntu (`apt`) and Fedora-family (`dnf`) prerequisite installation is supported. Cloud OS is installed into an isolated virtual environment under `/opt/cloud-os/.venv`. The development installer does not enable a root system service because that would also elevate the web terminal.

## Everyday commands

```text
cloud-os start
cloud-os status
cloud-os doctor
cloud-os version
cloud-os update-check
cloud-os update
```

## Updates

`cloud-os update-check` compares the installed package version with the latest GitHub Release. `cloud-os update` installs the latest release. Developers can explicitly update from the main branch with:

```bash
cloud-os update --source main
```

If no GitHub Release exists yet, the CLI explains that clearly instead of showing an unhandled traceback.

## Troubleshooting

Run:

```bash
cloud-os doctor
```

Installer failures use codes such as `I001` and updater failures use `U001`. The message includes the failed operation and, when possible, a direct recovery step.
