# Repeatable deployment and recovery plan

This is a recovery/design guide, not a redeployment command. Preserve the existing VM, passthrough and public access configuration unless an approved change is scheduled.

## Required inventory

Record Ubuntu release, VM CPU/RAM/disk, NVIDIA driver/CUDA compatibility, Tesla P100 16GB (or validated replacement), Docker/Compose version, Ollama version, Open WebUI image/version and volume name, LiteLLM image/version, `/opt/litellm/config.yaml` schema, model names/digests, `/mnt/ai-data/ollama/models` mount, and the existing private gateway/public access design. Store versions, not secrets.

## Reproduction shape

Install a compatible NVIDIA driver and validate `nvidia-smi`; install Docker with GPU access validated; install Ollama and set `OLLAMA_MODELS=/mnt/ai-data/ollama/models`; obtain approved model artifacts; start LiteLLM with its config mounted read-only where possible and only a localhost listener; start Open WebUI with its persistent Docker volume and a private connection to LiteLLM. Use the project’s existing pinned Docker commands/images as the source of truth after they are captured in a secure runbook. Do not copy credentials into shell history, compose files, reports or screenshots.

## Backup and restore

Back up the Open WebUI Docker volume consistently and test a restore into an isolated environment. Back up LiteLLM config with restrictive permissions, the operational folder, model inventory/digests and deployment manifests. Model files are large: decide explicitly whether they are backed up or recreated from verified sources. Encrypt backups, retain restore instructions separately from secrets, and test recovery periodically.

Restore order: provision VM/storage/GPU; restore validated software versions; restore config and secrets through the approved secret path; restore Open WebUI volume; ensure model storage is mounted; start services according to the existing deployment definition; run `ai_status.sh`, `/v1/models`, a low-load gateway evaluation and a browser/admin login check. Rollback means stop promotion, retain logs/config snapshot, restore the last known-good image/config/volume set, then repeat health checks.

## Automation path

First script inventory and read-only health/config validation, backup/restore verification, and benchmark/report execution. Later, represent VM/package/Docker/Ollama configuration in Ansible; use Terraform only for infrastructure that it actually owns; use CI/CD for linting config, image pin review and controlled staging deployment. Never make CI/CD directly change Proxmox passthrough or public exposure without explicit approval.
