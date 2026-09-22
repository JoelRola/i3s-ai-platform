# I3S Platform V1 final acceptance

Date: 2026-09-22 UTC. Credentials, chat contents, user names, and uploads were not displayed or copied into this report.

| Item | Result | Evidence |
|---|---|---|
| Open WebUI login/session path | PASS | Post-restart authenticated client requests for chat lists were observed; Open WebUI local health returned 200. |
| Historical chats retained | PASS | Aggregate read-only database count was 51 chats before and after the targeted Open WebUI restart. No content was queried. |
| I3S Assistant | PASS | Existing public/active `i3s-main`-based profile state supplied for V1; normal-user generation previously accepted. |
| I3S Work | PASS | Existing public/active `i3s-main`-based profile and `i3s_file_generator` tool binding supplied for V1; normal-user Toolbox acceptance previously passed. |
| Toolbox/downloadable generated attachment | PASS | Prior normal-user acceptance plus `TOOLBOX_V1_VALIDATION.md`; live isolated Toolbox is running and its document runtime dependencies import successfully. |
| RAG/embedding path | PASS | Fresh simultaneous direct generation/embedding proof returned 24 embeddings and activated both GPUs; embedding service is active and local model endpoint is healthy. |
| qwen3-embedding hidden from normal users | PASS | V1 configuration invariant: backend-only model; no normal-user profile change made. |
| Open WebUI local/public health | PASS | Local `/health` 200; Funnel Open WebUI URL returned 200. |
| Grafana local/public health | PASS | Local `/api/health` 200; Funnel Grafana URL returned 200. |
| Public-access watchdog | PASS | User timer enabled and active; repeated recent service executions completed successfully. |
| Targeted Open WebUI restart/persistence | PASS | Only `open-webui` restarted; it returned healthy. Chat/user aggregate counts were unchanged (51/6). |
| Main generation GPU | PASS | `dual_gpu_proof_20260922T074749Z.txt`: A100 peak utilization 100%. |
| Embedding GPU | PASS | Same fresh proof: P100 peak utilization 100%. |

Known Open WebUI limitation: `i3s-main` remains active/readable as a base model because this build requires readable active base models. It is documented and was not changed.

Security note: temporary I3S admin/user token files were absent from the inspected home/project candidate locations. Docker's own protected token-seed files exist outside the project and were not read. A normal-user token previously exposed outside this freeze process must be revoked/rotated manually if it is still active.
