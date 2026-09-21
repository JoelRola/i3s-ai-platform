# Supported Open WebUI user-UX change procedure

The installed Open WebUI exposes authenticated supported endpoints including `/api/v1/models/list`, `/api/v1/models/create`, model update/access endpoints, `/api/v1/tools`, `/api/v1/configs/models`, and tool-server configuration endpoints. These changes must be performed by an authenticated Open WebUI administrator through the Admin Panel or its API; never edit the database.

## Intended configuration

1. Retain `i3s-main` as the implementation alias to the existing main backend.
2. Create or update the user-facing workspace profile **I3S Assistant** based on `i3s-main` with normal-user read access.
3. Create or update **I3S Work** based on the same backend, with the `i3s_file_generator` tool enabled only for that profile and normal-user read access.
4. Remove normal-user read access, but retain admin/debug access, for `qwen3-embedding:4b`, raw Ollama models, experimental aliases, and the diagram specialist if Mermaid acceptance passes.
5. Set normal-user defaults/order to I3S Assistant then I3S Work using `/api/v1/configs/models`.

Before changing records, use authenticated `GET /api/v1/models/list`, `GET /api/v1/tools/list`, and `GET /api/v1/configs/models` to export the current supported configuration. Save that export outside Git as a rollback artifact. Apply each update through its corresponding documented API/Admin Panel action and verify as a normal user.

The required backup is `backups/open-webui-data-20260921T154332Z.tar.gz` (ignored by Git). A reload is not normally needed for workspace model access changes; if the UI remains stale, restart only `open-webui`, then verify local/public login, existing accounts/chats, I3S profiles, Toolbox binding, backend visibility, and Grafana/Funnel health.

## Mermaid acceptance

Ask I3S Assistant: “Return only a fenced Mermaid flowchart showing User → Open WebUI → LiteLLM → Ollama.” It passes when the response contains a `mermaid` fence, a valid flowchart declaration, and the three labelled edges. If it passes, retain the specialist diagram profile only for admin/testing.
