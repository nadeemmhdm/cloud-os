# Cloud OS Cybersecurity Learning Labs

Cloud OS Labs is a practical, host-safe cybersecurity and cloud-security learning environment built into the existing dashboard.

## Safety architecture

Labs never execute student commands against the production host. The runtime is a stateful simulator backed by a temporary per-session workspace under the Cloud OS data directory. Each session gets isolated `filesystem`, `logs`, `config`, `state`, and `output` directories.

Lab commands are allow-listed per exercise. Shell metacharacters, path traversal, absolute host paths, and external URLs are blocked. No lab command launches a host shell or contacts Internet/LAN targets.

The lab runtime never changes the host firewall, users, SSH configuration, network adapters, services, Registry, packages, boot configuration, production tunnels, Cloud OS authentication/RBAC, routes, DNS, production storage, or real credentials.

## Learning path

- Module 1 — Cloud Security Fundamentals: 6 practical labs + challenge
- Module 2 — Identity & Access Security: 6 practical labs + challenge
- Module 3 — Network Security: 6 practical labs + challenge
- Module 4 — Compute Security: 6 practical labs + challenge
- Module 5 — Storage & Data Security: 6 practical labs + challenge
- Final challenge — NovaCloud Ltd. Module 1–5 investigation

Total: **30 core labs + 5 module challenges + 1 final challenge = 36 exercises**.

## Practical workflow

1. Open **Labs**.
2. Choose a module and lab.
3. Read theory, objective, scenario, topology, tasks, hints, and AWS terminology mapping.
4. Select **Start Lab**.
5. Use the separate **LAB SANDBOX** terminal to inspect and change the simulated environment.
6. Select **Verify Lab** to run task-level checks against the actual sandbox state.
7. Review PASS/FAIL explanations and hints.
8. Retry or use **Reset** for a clean environment.
9. Complete the lab after every verification task passes.

## Lab Terminal

The Lab Terminal is separate from the unrestricted Cloud OS administrative terminal. It supports only the commands declared by the current lab plus harmless sandbox helpers such as `help`, `pwd`, `ls`, and synthetic `cat` fixtures.

Examples:

```text
cloud-lab resources
iam audit
sg remove db 3306 public
scan web-server
packages outdated
metadata protect require-token
bucket private customer-data
snapshot restore baseline
```

These commands modify only the current session state.

## Verification and progress

Each task defines a state requirement, points, hint, and failure explanation. Verification checks the state created by practical terminal actions; opening a page or clicking a button does not complete a task.

Cloud OS stores per-user status, attempts, best score, completion time, and last-opened time. Production audit logs record only lab/session events, not students' terminal command text.

## Owner management

The Cloud OS owner can open **Lab Management** to enable or disable labs, view aggregate completion/session statistics, and reset a user's saved lab progress. Student terminal command text is not exposed in the management UI.

## Error codes

- `LAB-1001` — sandbox initialization failed
- `LAB-1002` — runtime/definition unavailable
- `LAB-1003` — verification/state operation failed
- `LAB-1004` — session expired
- `LAB-1005` — unsafe/unsupported command blocked
- `LAB-1006` — reset failed
- `LAB-1007` — resource/rate limit exceeded
- `LAB-1008` — sandbox path violation

## Adding future labs

Definitions are split by module in `cloud_os/lab_defs_m*.py` and aggregated by `cloud_os/labs.py`. Keep future exercises declarative and host-safe. A practical command should inspect synthetic state or make one bounded simulated state change. Verification should read resulting state markers, never UI clicks.
