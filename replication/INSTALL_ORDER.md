# Install order

1. Install Ubuntu, NVIDIA driver/CUDA compatible with both GPUs, Docker Engine + Compose plugin, Ollama, Tailscale, `jq`, `curl`, `tar`, `sha256sum`, and systemd user services. Confirm Docker can use NVIDIA GPUs.
2. Clone this repository as a private repository. Copy `file_generation/.env.example`, `file_generation/file_service/.env.example`, and `monitoring/grafana.env.example` to untracked local files and create new values for every placeholder.
3. Discover replacement GPU UUIDs with `nvidia-smi --query-gpu=index,uuid,name --format=csv,noheader`. Do not reuse the UUIDs recorded for the source host. Bind main Ollama to the replacement A100 UUID and embedding Ollama to the replacement P100 UUID.
4. Install and enable the main Ollama system service and the embedding unit from `gpu_split_upgrade/ollama-embed.service`, adjusting paths, bind ports, and UUIDs. Keep model storage outside Git.
5. Restore models listed in `models_to_restore.txt`, start Tika, LiteLLM, Open WebUI, Toolbox, and the monitoring Compose stack using the manifests in this repository. Create the named Open WebUI volume before restoring data.
6. Configure Open WebUI through its supported admin UI/API: `i3s-main` remains readable/active as the base-model workaround; I3S Assistant and I3S Work remain public/active based on it; I3S Work retains only its existing Toolbox tool ID. Do not edit SQLite.
7. Configure Tailscale Serve/Funnel only after local health checks pass. Install watchdog and NVIDIA collector service/timer units. Complete [VALIDATION.md](VALIDATION.md).
