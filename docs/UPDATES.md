# Updates and Rollback

Cloud OS now provides two update commands:

```text
cloud-os update-check
cloud-os update
```

The default channel is the latest GitHub Release. `update-check` reports the installed and latest release versions. `update` fetches the release tag, upgrades the installed Python package, and reports whether the revision changed.

For development/testing only:

```text
cloud-os update --source main
```

If package installation fails, the updater attempts to restore the previous Git revision and reinstall it. This is an application-code rollback; persistent user data/configuration are not deleted.

A future production release should add signed/checksummed release artifacts, service-aware stop/start handling, persistent-data backup before migrations, post-restart HTTP health verification, and a formally tested rollback matrix.
