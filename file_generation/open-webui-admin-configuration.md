# i3s-work: one-time Open WebUI admin configuration

This deployment uses Open WebUI's built-in **Open Terminal** integration, not a community tool and not the Code Interpreter. The currently installed Code Interpreter has no generated-file attachment path for its Jupyter engine.

In **Admin Settings → Integrations → Open Terminal**, add exactly one system-level connection:

```text
Name: i3s-work files
URL: http://172.20.0.2:8000
Authentication: Bearer
API key: value from /home/jorola/i3s_ai_ops/file_generation/.env
Enabled: yes
Access grants: only the intended i3s-work users/group
```

Do not enable Calendar, Automations, email, system-administration tools, web search, or any other action integration for this profile.

In **Workspace → Models**, create the model profile through the UI/API (never by editing the SQLite database):

```text
Model ID: i3s-work
Base model: i3s-main (the existing LiteLLM qwen3.5:9b / A100 route)
Capabilities: enable native tool calling and Open Terminal only
System prompt: contents of i3s-work-system-instruction.txt
```

If the model editor requires an upstream ID rather than a base profile, use the same upstream model ID that the existing `i3s-main` profile uses. Keep `i3s-main` unchanged. In a new chat, select **i3s-work files** as the terminal, upload source files into that terminal workspace, and request the desired artifact. The model must call `display_file(path=...)` after creating it.
