# Sanitized dashboard screenshots

No automated screenshot/export mechanism is committed for the local Grafana instance. Do not install screenshot software or change Grafana solely to create images. The selected screenshots already published beside this note were manually reviewed for public-safe aggregate operational information.

If screenshots are added later, capture only the provisioned dashboards and redact or exclude all tokens, passwords, usernames, user/chat content, private IP addresses, Tailscale hostnames, internal URLs, and sensitive log payload. Suggested filenames are:

- `i3s-ai-platform-dashboard.png`
- `public-access-dashboard.png`
- `i3s-ai-logs-dashboard.png`

Current public-safe visuals:

- `architecture-overview.png`
- `grafana-platform-overview.png`
- `dual-gpu-monitoring.png`
- `benchmark-v1.png`

Before committing, review at full resolution and confirm the image contains only safe aggregate operational metrics. The dashboard definitions linked from the repository README remain the authoritative, reviewable source.
