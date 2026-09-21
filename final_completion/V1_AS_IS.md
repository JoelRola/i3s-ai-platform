# I3S Platform V1 — AS-IS snapshot (2026-09-21 UTC)

No secrets are recorded here.

## Live services

| Area | Observed state |
|---|---|
| Containers | `open-webui`, `litellm`, `tika`, `i3s-file-service`, `open-terminal-i3s-work`, `prometheus`, `grafana`, `loki`, `alloy`, `node-exporter`, `cadvisor`: running. |
| Systemd AI | `ollama.service` and `ollama-embed.service` active. `tailscaled.service` active. |
| Open WebUI | healthy, bound publicly on `0.0.0.0:8080`; environment build version `0a7c158...`; user supplied version target is 0.11.3. |
| LiteLLM/Tika | running loopback-only (LiteLLM 4000, Tika 9998). |
| Observability | Prometheus 9090, Grafana 3001, Loki 3100 loopback-only; Alloy running. |
| Public access | Funnel configured only for 443 → 127.0.0.1:8080 and 8443 → 127.0.0.1:3001. Both endpoints returned 200/302. External Cloudflare DNS returned A records. |
| GPUs | GPU 0 P100 16 GiB is idle; GPU 1 A100 40 GiB uses ~7.1 GiB. Preserve main/embedding split. |
| Disk | root 57 GiB, 42 GiB used, ~14 GiB available. Docker volumes ~1.64 GiB; build cache ~8.95 GiB. |

## Listening ports

Publicly bound: SSH 22 and Open WebUI 8080. Tailscale binds Funnel ports 443/8443 on its Tailscale addresses. Internal services are loopback-only: 11434 main Ollama, 11435 embed Ollama, 4000 LiteLLM, 9998 Tika, 9090 Prometheus, 3001 Grafana, 3100 Loki. Toolbox has no published port.

## Models

Main required models are present: `qwen3.5:9b` and `qwen3-embedding:4b`. Other locally retained models include qwen2.5 variants, qwen3:14b, gemma3 variants, mistral-nemo and llama3.2. None was deleted or moved.

## Source-control status

`/home/jorola/i3s_ai_ops` is not currently a Git worktree (`git status` reports no repository). CI files are prepared but cannot run remotely until this directory is initialized/published as a repository.
