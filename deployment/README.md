# Controlled release process

CI validates source only; it never deploys. Before a production release, use a reviewed commit, run the relevant compose configuration validation, take the automatic component-only backup created by `release.sh`, and deploy one component using `./deployment/release.sh monitoring` or `file-service`.

The script deliberately avoids global Docker restarts, reboots, secret files, and unrelated services. If a health check fails, restore the backed-up files, rerun the same targeted compose command, and record the incident. Review the backup before removing it.
