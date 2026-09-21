# Public deployment hardening checklist

Verification only: this checklist makes no firewall, Tailscale, Funnel, account or service change. Do not record keys, passwords, tokens or full authorisation headers in evidence.

| Control | Status | Priority | Verification location / notes |
|---|---|---|---|
| HTTPS/TLS valid and redirects understood | Needs verification | High | Open public URL in browser; inspect certificate/expiry. |
| Tailscale/Funnel exposure is intentional and minimal | Needs verification | High | Tailscale admin console and Funnel configuration; preserve current configuration. |
| Proxmox UI not public | Needs verification | High | External scan/review from authorised network; VM does not prove this. |
| Firewall permits only required paths/ports | Needs verification | High | VM firewall plus upstream/Tailscale policy review. |
| Open WebUI account creation policy | Needs verification | High | Open WebUI Admin Settings → Users/Auth. |
| Admin/user RBAC reviewed | Needs verification | High | Open WebUI Admin → Users; test least privilege account. |
| Raw model access hidden from normal users | Needs verification | High | Open WebUI model visibility and LiteLLM aliases; test as normal user. |
| Dangerous tools disabled for normal users | Needs verification | High | Open WebUI Admin → Tools/Functions; test a normal user. |
| LiteLLM master key protected | Needs verification | High | File ownership/mode and container environment; never print value. |
| Password reset procedure documented/tested | Not implemented | High | Create a consented test-account procedure. |
| Secure password hashing / auth provider reviewed | Needs verification | High | Open WebUI version documentation and configured auth provider. |
| Session/token expiry and revocation settings | Needs verification | High | Open WebUI Admin/auth configuration. |
| Audit logs available and retention known | Needs verification | Medium | Open WebUI/LiteLLM logs and Docker logging configuration. |
| Open WebUI Docker volume backup | Needs verification | High | Identify volume and run a restore-tested, encrypted backup procedure. |
| LiteLLM config backup | Needs verification | High | Back up `/opt/litellm/config.yaml` with restrictive permissions. |
| Operational folder backup | Needs verification | Medium | Back up `/home/jorola/i3s_ai_ops`, excluding secrets if ever added. |
| Log retention and rotation | Needs verification | Medium | Docker logging driver, journald and disk budget. |
| Rate limiting and abuse prevention | Needs verification | High | LiteLLM/Open WebUI settings or upstream reverse proxy/Tailscale controls. |
| Confidential-data tester warning | Confirmed | Medium | `tester_instructions.md`; reinforce in UI/onboarding. |
| Incident contacts, evidence handling and revocation | Not implemented | High | Write incident owner/contact/runbook outside public docs. |

## Recovery runbook outline

If Open WebUI fails: capture `docker ps`, `docker inspect`, and recent logs; confirm LiteLLM/Ollama health; preserve the database volume; restore only from a tested backup after diagnosis. If LiteLLM fails: capture config-safe logs and container state; verify `ollama` and localhost endpoint; restore known-good config only after review. If Ollama fails: capture `systemctl status` and journal excerpts, check disk/GPU and model path; do not delete models; restore service/config only through an approved maintenance action. For any incident, restrict public access through established procedures, preserve timestamps, rotate exposed credentials through their owners, and document recovery verification.
