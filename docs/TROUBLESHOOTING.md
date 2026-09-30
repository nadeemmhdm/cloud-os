# Troubleshooting

Start with:

```bash
cloud-os doctor
```

Check Python, storage permissions, SSH/cloudflared availability, configured port, and service state.

If the dashboard does not load, verify the Cloud Os process is running and that the configured host/port is reachable. If remote access fails while local access works, inspect the tunnel/VPN/reverse-proxy configuration rather than exposing the development server directly.

For boot-start issues, inspect the Windows startup task/service or Linux systemd unit and its logs. Do not delete persistent configuration as a first troubleshooting step.
