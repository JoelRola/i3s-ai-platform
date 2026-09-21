# I3S final project results

## System

- Source host: `brain2`; RAM: 14 GiB; GPUs: NVIDIA A100-SXM4-40GB and Tesla P100-PCIE-16GB.
- Generation model: `i3s-main` -> `qwen3.5:9b`; embedding model: `qwen3-embedding:4b`.
- Major services verified running: main Ollama, embedding Ollama, Open WebUI, LiteLLM, Tika, Prometheus, Grafana, node-exporter, and cAdvisor.

## Performance and GPU architecture

- Warm TTFT p50/p95: 0.5843 / 0.5998 s (core 15-request run).
- Generation: 59.50 tok/s mean (core); 62.08 tok/s mean (focused load).
- Focused 1/2/4/8-user load: 75/75 success, 0% error; total latency p50/p95 17.8701 / 22.1491 s; max stable tested concurrency: 8.
- GPU isolation and simultaneous proof: PASS. A100 performed qwen3.5 generation (77% sampled peak); P100 performed qwen3-embedding batch work (100% sampled peak). CUDA backend logs confirm the intended physical devices; no Vulkan fallback was observed.

## Observability

- Prometheus has healthy `prometheus`, `node`, and `cadvisor` targets; GPU, service-health, and genuinely exposed LiteLLM gauges are collected.
- The primary dashboard is `I3S AI Platform` at `monitoring/grafana/dashboards/i3s-ai-platform.json`.
- Validated alerts: RAM >90%, disk >85%, target down, GPU VRAM >95%.
- This LiteLLM build does not expose request/error counters, TTFT, latency, or token metrics, so no fabricated latency/throughput panels or alerts were created.

## Reproducibility and final status

- Migration bundle retained unchanged: `~/i3s_migration_20260915.tar.gz`.
- Replacement-VM restore, validation, dual-GPU proof, and comparison benchmark are **not run**: no replacement VM connection or identity was supplied/available in this workspace.

**FINAL STATUS: INCOMPLETE — source-system acceptance passes; migration-dependent acceptance cannot be marked PASS until a replacement VM is available and restored.**
