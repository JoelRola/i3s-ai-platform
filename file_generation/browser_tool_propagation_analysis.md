# Browser model-default Tool propagation — 2026-09-16

## Persisted state (read-only verification)

- `i3s-work.info.meta.toolIds`: `["i3s_file_generator"]`
- `i3s-main.info.meta.toolIds`: absent
- `i3s_file_generator` has a public read access grant and is returned by the normal authenticated `GET /api/v1/tools/` endpoint.

No model or service configuration was changed during this investigation.

## Exact installed Open WebUI 0.11.3 browser path

The installed browser bundle (`/app/build/_app/immutable/chunks/CS9gMiwt.js`) contains the model-selection initializer equivalent to:

```javascript
if (selectedModel.info.meta.toolIds) {
  const eligible = selectedModel.info.meta.toolIds
    .filter(id => loadedTools.find(tool => tool.id === id));
  selectedToolIds = eligible;
}
```

The same bundle serializes the selected Tool state into the normal chat payload as:

```javascript
tool_ids: selectedToolIds.length > 0 ? selectedToolIds : undefined
```

The backend normal chat middleware then reads only the request field:

```python
tool_ids = form_data.pop("tool_ids", None)
```

It resolves database-backed Tools only when that field is present. It does not independently fall back to `model.info.meta.toolIds` for an ordinary browser chat request.

`meta.toolIds` is therefore a browser-side default: it is copied into the browser's selected Tool state during model selection, filtered against the browser's current `/api/v1/tools/` store, and only then sent to the server as `tool_ids`.

## Cause of the observed failure

The known-good authenticated API validation explicitly sent `tool_ids: ["i3s_file_generator"]`. It consequently exposed `create_xlsx`.

The failed browser conversation did not send that chat-level field. Its model received no database Tool definition and correctly reported that it had no file creation tool.

This is not a file-service, model, model-mapping, API-key, or Tool permission failure. The model/tool update happened after the browser application's model/Tool stores were already loaded, or the test used a conversation whose selected-tool state was initialized before the new model default was available.

## Supported recovery / acceptance test

1. Hard-refresh the Open WebUI page while signed in (this reloads `/api/models` and `/api/v1/tools/`).
2. Start a **new** chat, select `i3s-work`, and do not select a terminal or a Tool manually.
3. Request `test_finance.xlsx` as in the acceptance test.

For an administrator-visible diagnostic, the chat request in browser developer tools must include:

```json
{"tool_ids":["i3s_file_generator"]}
```

Once that field is present, the normal server middleware injects the Tool's `create_xlsx` function. Browser artifact rendering still needs this one real-browser acceptance test; no API-only request can prove the browser attachment UI.

## Feature flags

For a database-backed Tool, the model-default `toolIds` branch runs before and independently of the `defaultFeatureIds` checks for web search, image generation, and code interpreter. No extra capability/default-feature flag is required to propagate `i3s_file_generator`.

## Safety

No change was made to `i3s-main`, qwen3.5:9b, the isolated file service, Docker isolation, or Open Terminal.
