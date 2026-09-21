# Source-system final technical result

- A100 isolated: **PASS**. `ollama.service` is pinned to UUID `GPU-f60893db-9b34-48da-859c-ad6639f545ef` with `OLLAMA_LLM_LIBRARY=cuda_v12`; runner logs identify `NVIDIA A100-SXM4-40GB` as CUDA0.
- P100 isolated: **PASS**. `ollama-embed.service` is pinned to UUID `GPU-685c9973-bece-68da-c697-474881571cee` with `OLLAMA_LLM_LIBRARY=cuda_v12`; runner logs identify `Tesla P100-PCIE-16GB` as CUDA0.
- Simultaneous workload: **PASS**. qwen3.5 generation and 24 qwen3-embedding batch inputs completed together; sampled A100 peak utilisation was 77%, P100 peak utilisation 100%.
- qwen3.5 warm benchmark (15 requests, short/medium/long): TTFT p50 0.5843 s, p95 0.5998 s; generation mean 59.5031 tok/s; error rate 0%.
- Focused load test (1/2/4/8 users, 75 requests): 75/75 successful; total latency p50 17.8701 s, p95 22.1491 s; TTFT p50 0.5873 s, p95 0.5925 s; generation mean 62.08 tok/s; maximum tested stable concurrency 8.
- Peak simultaneous proof VRAM: A100 7805 MiB; P100 5817 MiB. These are sampled proof peaks, not model-residency capacity claims.
- Prometheus: healthy targets `prometheus`, `node`, and `cadvisor`; real GPU, private service-health, and LiteLLM active-request/user metrics ingest correctly.
- Grafana: provisioned dashboard `I3S AI Platform` saved at `monitoring/grafana/dashboards/i3s-ai-platform.json`.
- LiteLLM limitation: installed version exposes active-request and active-user gauges, not request counters, error counters, TTFT, latency, or token metrics. Unsupported metrics were deliberately not graphed or alerted.

Evidence: `source_baseline.txt`, `gpu_isolation.txt`, `dual_gpu_proof.csv`, `dual_gpu_proof.txt`, and `../benchmark/results/`.
