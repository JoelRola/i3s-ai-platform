# Architecture

`Open WebUI (0.0.0.0:8080)` is the authenticated user interface and owns `/app/backend/data` in Docker volume `open-webui`. It routes `i3s-main` through loopback-only LiteLLM (`127.0.0.1:4000`), which calls main Ollama (`127.0.0.1:11434`). Main Ollama serves `qwen3.5:9b` on the A100.

Embedding Ollama is a separate systemd service on `127.0.0.1:11435`, serving `qwen3-embedding:4b` on the P100. It is backend-only: do not expose it as a normal-user Open WebUI model.

I3S Work includes `i3s_file_generator`, which reaches the internal-only `i3s-file-service` Docker network. Tika is loopback-only at `127.0.0.1:9998`. Prometheus, Grafana, Loki and Alloy provide monitoring; Grafana is loopback-only at `127.0.0.1:3001`.

Tailscale Funnel is the only public ingress: 443 proxies Open WebUI and 8443 proxies Grafana. The public watchdog observes availability and alerts; it never changes Funnel.
