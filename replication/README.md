# I3S Platform V1 replication package

This package rebuilds the I3S pilot-production platform on a new Ubuntu VM. It contains configuration and operating instructions only: no credentials, Open WebUI data, uploads, model blobs, monitoring state, or backups are in Git.

Follow [INSTALL_ORDER.md](INSTALL_ORDER.md) on a clean host, then [VALIDATION.md](VALIDATION.md). Restore production user data only through [RESTORE.md](RESTORE.md). Recreate every secret locally from the examples; never copy a value from this repository.

The deployed platform is Open WebUI + LiteLLM + two independently bound Ollama services, with the generation service on the A100 and embedding service on the P100. Open WebUI profiles are I3S Assistant and I3S Work; preserve their existing ACL design during a migration.
