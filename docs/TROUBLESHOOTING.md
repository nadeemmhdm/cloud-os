# Troubleshooting

Start with:

```bash
cloud-os doctor
```

Check Python, storage permissions, SSH/cloudflared availability, configured port, and service state.

If the dashboard does not load, verify the Cloud OS process is running and that the configured host/port is reachable. If remote access fails while local access works, inspect the tunnel/VPN/reverse-proxy configuration rather than exposing the development server directly.

For boot-start issues, inspect the Windows startup task/service or Linux systemd unit and its logs. Do not delete persistent configuration as a first troubleshooting step.

## Windows install/update recovery

If Cloud OS is already running or a previous installation/update was interrupted, try the normal repair path first:

1. Stop Cloud OS normally.
2. Run `cloud-os doctor` when the command is available.
3. Retry the installer or updater from an Administrator PowerShell window.
4. Reboot Windows if a stale process or file lock prevents the repair.

### Last-resort clean reinstall

If the installer still cannot repair the installation, the Windows installer source checkout can be recreated.

The installer checkout is located at:

`C:\ProgramData\CloudOs`

Before removing it, make sure Cloud OS is stopped and back up anything you intentionally stored inside that directory. Then remove the `CloudOs` checkout folder using Windows File Explorer or Administrator PowerShell and run the official Cloud OS Windows installer again.

The fresh installer recreates the checkout, installs the current Cloud OS package, runs setup, configures autostart, and performs diagnostics.

### Data safety

The clean-reinstall procedure is intended for the source checkout only. Do not remove separate user storage, backups, credentials, configuration, or other persistent Cloud OS data unless you intentionally want a complete data purge.

After reinstalling, verify the installation with:

```powershell
python -m cloud_os.cli doctor
python -m cloud_os.cli status
```

If `python` is not available on PATH, use the exact Python executable path displayed by the installer.

If the clean reinstall still fails, keep the complete installer output beginning at the first `[ERROR ...]` message so the failing stage can be diagnosed.
