# V1 UX, Git and CI/CD continuation — 2026-09-21 UTC

## Open WebUI safety

The active persistent volume is `open-webui` mounted at `/app/backend/data`. Before any change, a read-only volume backup was created at `backups/open-webui-data-20260921T154332Z.tar.gz` with a SHA-256 sidecar. Size: 996 MiB. This backup is Git-ignored.

Supported installed APIs were inspected from router definitions. Model listing, model creation/update/access, tool listing, and model defaults are authenticated endpoints. Anonymous model listing returned HTTP 401. No database was read or edited, no credentials were extracted, and no Open WebUI restart was performed because no authenticated supported model/profile update could be safely made.

The I3S main LiteLLM route accepted a short Mermaid request with HTTP 200. The response was deliberately not persisted in logs. Full user-profile Mermaid acceptance remains pending the authenticated Admin Panel/API change described in `openwebui_user_ux.md`.

## Git and GitHub

Git preparation is complete: `.gitignore`, empty-value environment template, safety review, README, VERSION 1.0.0, CHANGELOG, CI, and manual-release handoff workflow exist. Repository creation/commit is blocked in this workspace because `.git` is mounted read-only; Git cannot write config/index. No commit, tag, remote, or push was created.

`gh auth status` reports the stored GitHub credential for `JoelRola` is invalid. Re-authenticate interactively, never in chat: `gh auth login -h github.com`.

## Local validation

Python compilation, shell syntax, Grafana JSON parsing, both Compose configurations, and Toolbox prohibited-call regression checks passed. No production deployment occurred.
