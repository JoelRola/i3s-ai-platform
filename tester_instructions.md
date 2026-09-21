# Testing the I3S AI platform

Choose an alias when starting a new chat:

| Alias | Use |
|---|---|
| i3s-fast | Normal/default questions |
| i3s-balanced | Better reasoning |
| i3s-coding | Programming |
| i3s-diagrams | Mermaid, process and architecture diagrams |

Use one task per chat. Do not switch models inside the same chat; start a new chat to compare aliases. If a response is malformed, regenerate once. If it remains malformed, record the model, prompt (sanitised), UTC time and error in `tester_feedback.csv`.

Models do not have internet access unless a web search tool is explicitly enabled. Claims of browsing or executing tools are not proof that an action happened. Verify important answers. Mermaid output is diagram text, not real image generation.

Never paste confidential production secrets during testing. Use fictional examples and sanitise any feedback. Keep security testing high-level: assess refusal and safe alternatives without requesting operational attack instructions.

Feedback fields: use an ISO UTC timestamp, a tester nickname, the alias, and a brief prompt type. Use yes/no for worked and language_correct. Rate quality and speed from 1 (poor) to 5 (excellent). Put the sanitised prompt, time and error details in error_or_issue/notes; quote CSV fields containing commas or newlines. Record slow, misleading or incorrect answers as well as malformed ones.
