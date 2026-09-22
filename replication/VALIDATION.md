# Validation

Run these after installation or a controlled restore:

```bash
curl -fsS http://127.0.0.1:8080/health
curl -fsS http://127.0.0.1:3001/api/health
curl -fsS http://127.0.0.1:9998/tika
systemctl is-active ollama.service ollama-embed.service tailscaled.service
systemctl --user is-active i3s-public-access-watchdog.timer
docker compose -f monitoring/docker-compose.yml config --quiet
docker compose -f file_generation/file_service/compose.yaml config --quiet
python3 benchmark/ai_platform_benchmark.py --dual-proof
```

The dual-GPU proof must report PASS and non-zero utilization for both GPUs. Test an ordinary user login, retained chats after a targeted Open WebUI restart, both I3S profiles, Toolbox attachment download, a RAG upload/query, and that `qwen3-embedding:4b` is not offered to ordinary users. Check the two configured Funnel URLs from an external client. Do not expose credentials in terminal history or reports.
