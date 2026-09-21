# Kubernetes readiness — V1 evidence only

No Kubernetes component is installed or deployed.

| Component | Direction | Current evidence / migration implication |
|---|---|---|
| Open WebUI | MODIFY | Stateful volume; pin an immutable image rather than `main`. |
| LiteLLM | MODIFY | Loopback container today; externalize secret/config and pin image. |
| Ollama/inference | REPLACE | Host systemd service with A100 affinity; requires GPU-aware workload design. |
| Embeddings | REPLACE | Separate P100 systemd service; preserve dedicated GPU scheduling. |
| Toolbox | REUSE | Isolated container, dedicated volume, internal network; retain least privilege. |
| Tika | REUSE | Internal-only service. |
| Prometheus/Grafana/Loki/Alloy | MODIFY | Existing containers/config; add persistent volumes and workload policies. |
| Storage/database/vector-RAG | INTRODUCE | Current Open WebUI volume is a single-host dependency; durable DB/PV architecture is not yet evidenced. |
| Ingress | REPLACE | Current public path is Tailscale Funnel; no cluster ingress design validated. |
| GPU scheduling | INTRODUCE | Must explicitly prevent generation/embedding co-location changes. |
| CI/CD | MODIFY | Source validation now exists; deployment remains reviewed and targeted. |

Current single points of failure: brain2 host, its disks, Tailscale Funnel/DNS control plane, Open WebUI volume, LiteLLM container/config, both Ollama systemd services, and each physical GPU. Migration discovery must establish data ownership, backup/restore tests, RAG/vector storage, identity, secret management, and immutable image versions before design commitments.
