# Contributing to Cloud Os

Thank you for contributing.

## Development setup
1. Fork or clone the repository.
2. Use Python 3.10 or newer.
3. Create a virtual environment.
4. Install the project in editable mode.
5. Keep changes focused and add tests for behavior changes.

## Standards
- Do not commit passwords, API tokens, tunnel credentials, private keys, or personal data.
- Preserve Windows 10/11 and Linux compatibility.
- Validate filesystem paths before access.
- New privileged actions require authorization checks and audit logging.
- Keep the UI responsive and accessible.
- Update documentation when commands, configuration, APIs, or permissions change.

## Pull requests
Explain the problem, implementation, security impact, test results, and any migration requirements. A passing review does not replace platform-specific testing.
