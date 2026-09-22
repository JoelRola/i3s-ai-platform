# I3S Platform V1 final freeze

Date: 2026-09-22 UTC. **READY FOR v1.0.1.** No production architecture, branding, ACL structure, GPU assignment, users, chats, or Funnel configuration was changed during this freeze.

## Architecture and functionality

Open WebUI v0.11.3 is public at the controlled Funnel endpoint and uses its `open-webui` Docker volume for persistent data. LiteLLM (loopback 4000) routes `i3s-main` to main Ollama (loopback 11434). Main `qwen3.5:9b` runs on the A100; separate systemd embedding Ollama (loopback 11435) serves backend-only `qwen3-embedding:4b` on the P100. I3S Assistant and I3S Work remain public/active on `i3s-main`; I3S Work retains `i3s_file_generator`. Tika and the internal Toolbox remain deployed. Prometheus, Grafana, Loki, Alloy, node-exporter, cAdvisor, the NVIDIA collector, and the conservative public-access watchdog are active.

Observed deployed versions: Docker Engine 29.8.0; Compose v5.5.1; Ollama 0.34.0; systemd 259.5; Open WebUI v0.11.3 (`main` image tag); Grafana 12.3.1; Loki 3.7.2; Alloy 1.19.2; Prometheus 3.8.1; Tika 3.2.3.0. Floating tags for Open WebUI and LiteLLM remain a known supportability limitation; pin immutable digests in a separately reviewed upgrade.

## Validation and URLs

- GPU split: fresh proof `dual_gpu_proof_20260922T074749Z.txt` and CSV record simultaneous generation plus 24 embeddings, with A100 and P100 peak utilization both at 100%.
- CI: GitHub Actions **I3S CI PASS**, run [35701377174](https://github.com/JoelRola/i3s-ai-platform/actions/runs/35701377174), commit `66343be189f9a8616b69d5cecf83a19cb641bc60`.
- Local health: Open WebUI `/health`, Grafana `/api/health`, and Tika `/tika` all returned HTTP 200. Public Funnel health: `https://brain2.tailcedd84.ts.net` and `https://brain2.tailcedd84.ts.net:8443` both returned HTTP 200.
- Open WebUI targeted restart: healthy afterward; read-only aggregate counts remained 51 chats and 6 users.
- Final non-deploying checks PASS: Python and shell syntax, Compose configuration, dashboard JSON, Toolbox runtime dependency imports, `git diff --check`, and tracked-source secret scan. The standalone host artifact script was not runnable because optional document libraries are intentionally absent from the host; the running isolated Toolbox image contains them and prior Toolbox acceptance passed.

## Security, backup, and rollback

Repository visibility is **PRIVATE**. The tracked source scan found no committed credentials, databases, backups, model blobs, uploads, or runtime data; `.gitignore` excludes these. Temporary I3S admin/user token files were absent from inspected candidate locations. Do not disclose or reuse a previously exposed normal-user token: revoke/rotate it manually if it remains active.

Fresh backup (not committed): `final_completion/backups/open-webui-data-20260922T074927Z.tar.gz`.

SHA256: `365aa1c02c9b5f2ef723c0af129edbece2fd281c5c4ea7f0ef67cc5834e02564`.

The archive was read successfully (248 entries); no restore was performed. Exact destructive rollback procedure is in `replication/RESTORE.md`; retain prior backups and make a pre-restore backup first.

## Limits and deferred work

The documented readable/active `i3s-main` visibility is an Open WebUI limitation. No Kubernetes, Whisper, vision capability, automatic deployment, or production restore test was introduced. Pin floating image tags/digests and rotate the previously exposed normal-user token in a future controlled maintenance change.

Replication instructions are in `replication/`. They document Ubuntu dependencies, secrets to recreate (never values), Docker/Compose, persistent volume, LiteLLM, both Ollama services, host-specific GPU rediscovery, Tika, Toolbox, monitoring, systemd, ports, Funnel, model restores, Open WebUI configuration, health checks, acceptance, and rollback.

## Git freeze status and release commands

Expected final Git status after committing/pushing this package: `## main...origin/main` with no modified or untracked tracked files. Runtime backups remain ignored by design.

```bash
cd /home/jorola/i3s_ai_ops
git status --short --branch
git pull --ff-only origin main
git tag -a v1.0.1 -m 'I3S Platform V1.0.1 freeze'
git push origin v1.0.1
```

Run the commands only after confirming the clean status shown above; no tag was created by this freeze.
