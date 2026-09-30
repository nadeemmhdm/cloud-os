# Updates and Rollback

Cloud Os intends to use GitHub Releases as the update source. A production update flow should verify version metadata and package integrity, create a recoverable backup, apply the update, restart the service, run a health check, and roll back if validation fails.

The complete verified automatic update/rollback pipeline is not yet production-ready. Do not describe development update hooks as a security boundary or guaranteed recovery mechanism.
