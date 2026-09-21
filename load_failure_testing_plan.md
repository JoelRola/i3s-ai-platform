# Load and failure testing plan

No failure is simulated by this plan. Test on a quiet maintenance window with a named operator, observer, rollback owner, backups verified and no public-workday dependency.

| Stage | Users | Goal | Gate to advance |
|---|---:|---|---|
| Safe first test | 1 | Baseline latency/TTFT, response quality and resource sampling. | No timeout/error; capacity remains comfortable. |
| Safe second test | 2 concurrent | Measure queueing and throughput under current parallel limit. | p95 and errors acceptable; no sustained resource pressure. |
| Later | 5 | Controlled capacity observation. | Explicit approval and user impact plan. |
| Later | 10 | Find practical queue/timeout boundary. | Isolated window and clear stop thresholds. |
| Future/controlled only | 20 | Characterise failure behaviour, not normal operation. | Isolated environment or maintenance window, approval and rollback. |

Measure successful/failed requests, p50/p95/maximum latency, TTFT, tokens/sec, queue symptoms, completion quality, GPU utilisation/VRAM/power/temperature, CPU/RAM/swap, disk, loaded models, container restarts and service logs. GPU saturation appears as sustained high utilisation with growing latency/queueing; VRAM pressure appears near capacity, allocation failures or offload/slowdown. RAM pressure appears as low available memory, rising swap/OOM events or latency instability. Compare short, medium and long prompts to locate context-window degradation: lost instructions, truncation, rising latency or quality regression.

Later controlled failure scenarios: restart Open WebUI, LiteLLM or Ollama one at a time; create and remove a bounded dummy file on a dedicated test filesystem to test disk warnings; terminate a model process only in a maintenance window; temporarily disconnect the local gateway. Expected behaviour: user-facing error rather than silent fabrication, health checks detect the component, data/config stay intact, and recovery returns aliases and a test request without database loss. Capture timestamps and logs before/after each action.

Do not run high concurrency, restart services, fill disks, kill processes, alter firewall/Tailscale/Funnel, or perform destructive tests on a public workday or while users depend on the service.
