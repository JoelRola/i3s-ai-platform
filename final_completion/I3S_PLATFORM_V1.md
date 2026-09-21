# I3S Platform v1 — release evidence (2026-09-21 UTC)

## Release marker

**I3S Platform v1: PARTIAL.** Core pilot services, public endpoints, watchdog timer, Prometheus alert, and dashboard provisioning are healthy. V1 remains PARTIAL until actual authenticated normal-user Toolbox attachment acceptance is performed.

## Version inventory

Open WebUI uses the `ghcr.io/open-webui/open-webui:main` image and reports build `0a7c158...` (the requested installed product version is 0.11.3). LiteLLM is `main-latest`; Grafana 12.3.1; Loki 3.7.2; Alloy 1.19.2; Prometheus 3.8.1; Tika 3.2.3.0. These floating application tags are a V1 supportability limitation: pin immutable versions before a later upgrade.

Main model `qwen3.5:9b` remains assigned to A100. Embedding model `qwen3-embedding:4b` remains assigned to P100. No model deletion, movement, Kubernetes deployment, or vision-model deployment occurred.

## Capability state

Document-generation acceptance returned 200 from the live isolated service for DOCX (3×3 table), XLSX/formulas, Unicode/wrapped PDF, PPTX, CSV, PNG chart, and text. The Open WebUI tool source uses the official upload handler to attach artifacts. Real authenticated Open WebUI attachment acceptance remains required.

Image metadata/OCR/resize/convert, ZIP create/list/extract, FFprobe audio/video inspection, keyframe extraction, and optional transcription endpoints are implemented. Archive extraction is bounded to 200 files/100 MiB, rejects traversal/backslash/symlink members, and extracts only below its dedicated archive subdirectory. Semantic visual understanding is **NOT DEPLOYED**.

Faster-Whisper Small is documented as CPU/int8 only (~0.5 GB model storage, typically 1–2 GB RAM for short work; usable English and Portuguese baseline). The runtime is ready but no approved model was staged due to available disk and offline-volume requirements; transcription is **MODEL READY / FUNCTION UNTESTED**.

## Observability and security

The active user-systemd public watchdog runs every minute and writes local/backend, Cloudflare DNS, public Open WebUI, and public Grafana health/HTTP/latency/consecutive-failure metrics. The active Prometheus alert fires after three failures and the provisioned Public Access dashboard exposes the metrics. The watchdog intentionally never resets Funnel. Grafana/Prometheus/Loki/Alloy remain in place. Toolbox is non-root, root-read-only, capability-dropped, resource-limited, internal-only, has no Docker socket or host mount, and accepts no URL/shell operation.

## Known limitations / next controlled actions

1. Run authenticated i3s-work browser acceptance for Open WebUI-owned attachments and role/model visibility.
2. Supply the approved wallpaper path before branding asset deployment.
3. Initialize/publish the source repository to activate GitHub Actions; do not make CI deploy production.
4. Update migration staging again after the remaining user acceptance; no final archive was rebuilt.
