# Access and auditability — V1

Open WebUI authentication and its admin/normal-user role model remain the access boundary; no SQLite edits were made. The I3S Toolbox source is intended for the `i3s-work` profile only, and its proxy persists generated artifacts through the official Open WebUI upload handler, yielding Open WebUI-owned file IDs rather than a direct file-service URL.

Grafana is only exposed through the intended Funnel port 8443. Prometheus, Loki, LiteLLM, Tika, Ollama, and Toolbox are not publicly published.

Alloy forwards Docker logs and the two Ollama journals to Loki with token/password/API-key redaction. Retain metadata-oriented audit fields where components natively log them: timestamp, available account/user identifier, profile/model, tool/operation, outcome/status, and native request ID. Do not log prompts, source document content, base64 artifacts, bearer tokens, or secrets.

Correlation foundation: Open WebUI uploads provide file IDs and chat/message context to the Toolbox attachment bridge. No safe, supported end-to-end shared request-ID header between Open WebUI, LiteLLM, and Toolbox was evidenced, so none was invented. A future component upgrade should preserve native `X-Request-ID`/request IDs where exposed and add them to structured logs without changing protocol contracts.

Normal-user model visibility was not changed: supported admin API authentication was not available in this run, and manually editing SQLite is prohibited. The expected target is only `I3S Assistant` and `I3S Work`; retain any diagram profile for admin/test only after an authenticated admin verifies that i3s-main/work Mermaid quality is acceptable.
