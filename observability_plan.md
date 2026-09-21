# Observability plan (no monitoring stack installed)

## Monitor now

Use `ai_status.sh` for a point-in-time service/GPU/disk/RAM check and `watch_ai.sh` during tester activity. Benchmark CSV records provide request count, latency, errors, approximate throughput, sampled GPU VRAM/utilisation, RAM and CPU load. Docker inspection supplies container state, health and restart count; `systemctl` supplies Ollama state; `ollama ps` supplies loaded models.

Track request count; request latency including p50/p95; API error and timeout rate; active model and loaded Ollama models; GPU utilisation, VRAM and power draw; CPU and RAM; root/model-storage disk; Open WebUI, LiteLLM and Ollama uptime; and container restart count. Active users may not be exposed by the current components and should be marked unavailable rather than inferred from request count.

## Later Prometheus/Grafana design

Prometheus should scrape node_exporter (CPU, memory, filesystems/load), an NVIDIA exporter (prefer DCGM exporter if compatible; otherwise nvidia_gpu_exporter), cAdvisor or Docker metrics, LiteLLM metrics if the deployed version exposes them, and a small authenticated health/metrics adapter only if needed. Grafana should show a platform overview, per-alias latency/throughput/errors, GPU and host resources, containers/services, and capacity trends. Keep metrics endpoints private; no public listener is required.

## Alerts to design

Alert on VRAM >95%, RAM >90%, either disk >85%, p95 latency doubling against a stable baseline, API error rate >5%, model timeout rate above an agreed baseline, Open WebUI down, LiteLLM down, Ollama down, or an unexpected container restart. Use sustained windows and a minimum request count for latency/error alerts to avoid false positives. Define an owner, severity and runbook link for every alert before enabling paging.
