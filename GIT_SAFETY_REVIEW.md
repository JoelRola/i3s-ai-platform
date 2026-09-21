# Git safety review — 2026-09-21

No secret values are included in this review.

| Category | Paths/patterns found or expected | Remediation |
|---|---|---|
| Runtime secrets | `file_generation/.env`, compose environment files, `monitoring/grafana.env` | Ignore all `.env*` except templates; ignore Grafana environment file. |
| Open WebUI data | Docker volume `open-webui` and the new volume backup | Never commit volumes/databases/user files; ignore `backups/` and database patterns. |
| Observability data | Prometheus/Loki/Grafana/Alloy Docker volumes, textfile state | Ignore data/state paths; retain only configuration and dashboards. |
| Models | Ollama storage and optional Whisper model data | Do not commit model weights/blobs; ignore model/cache patterns. |
| User/generated files | Toolbox volume and generated attachments | Never commit generated/user content; ignore generated/upload/data paths. |
| Archives | Migration and volume archives | Ignore tar/zip archives; final migration archive remains untouched. |
| Logs/caches | Logs, Python caches, temporary/IDE files | Ignore generated logs/caches and editor metadata. |

Safe-to-commit material is source code, Compose files, sanitized configuration, dashboards, service/unit templates, deployment procedure, documentation, and environment-variable templates with empty values. A filename/pattern secret scan is required before every release; findings must be remediated rather than printed.
