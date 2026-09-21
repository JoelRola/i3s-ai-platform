# I3S AI Platform

I3S AI Platform is a pilot-production internal AI workspace built around Open WebUI, local inference, document tooling, and observability.

## Architecture

- **Open WebUI** provides authenticated user chat, RAG, and workspace profiles.
- **LiteLLM** routes generation requests to local inference.
- **Ollama** serves `qwen3.5:9b` for generation and `qwen3-embedding:4b` for embeddings.
- **I3S Toolbox** is an isolated service for documents, spreadsheets, PDFs, presentations, charts, OCR, image processing, safe archives, and media foundations.
- **Tika** supports document extraction.
- **Prometheus, Grafana, Loki, and Alloy** provide metrics, dashboards, and redacted logs.

Generation is assigned to an A100 GPU. Embeddings remain separately assigned to a P100 GPU. This split is an operational invariant.

## Capabilities

The intended user experience is I3S Assistant for general chat, reasoning, RAG, web/coding where configured, and Mermaid diagrams; and I3S Work for the same capabilities plus the I3S Toolbox. Backend models are not normal-user products.

## Security and operations

Toolbox is internal-only, non-root, read-only-root, capability-dropped, resource-limited, and has no Docker socket or host filesystem mount. Public access is limited to the intended Tailscale Funnel endpoints. Credentials, runtime data, user files, model blobs, and backups are excluded from Git.

The public-access watchdog records local backend, public DNS, and HTTPS health, alerts after repeated failures, and never repairs Funnel automatically.

## Repository layout

- `file_generation/` — Toolbox service and Open WebUI integration.
- `monitoring/` — Prometheus, Grafana, Loki, Alloy, dashboards, alerts.
- `deployment/` — reviewed, targeted manual release helper.
- `architecture/` — current architecture and Kubernetes readiness evidence.
- `final_completion/` — V1 evidence and validation reports.
- `.github/workflows/` — non-deploying CI validation.

## CI/CD

GitHub Actions validates source, shell/Python syntax, Compose configuration, dashboards, and Toolbox security regressions. CI never deploys. Production releases remain reviewed and manual: validated commit, component backup, targeted update, health check, and rollback using the retained backup.

## V1 status and direction

V1 is a stable pilot-production baseline. Open WebUI profile visibility changes are applied only through supported authenticated administration APIs/UI, never by editing SQLite. Kubernetes/HA is a future migration direction documented from current evidence; it is not deployed here.
