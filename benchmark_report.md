# Local LLM benchmark report

## Executive summary

Benchmarked a self-hosted local LLM deployment across latency, throughput, memory usage and concurrent-user workloads to estimate safe serving limits.

This report contains 27 requests: 27 successful (100.0%) and 0 failed (0.0%). Aggregate successful-request latency: p50 39.81 s, p95 75.08 s, mean 42.64 s. Results are workload-specific, not production capacity guarantees.

## Architecture

Users → Open WebUI → LiteLLM → Ollama → Local Models → P100 GPU.

## Tested models

| Alias | Requests | Successful | Success rate | Mean latency | p50 | p95 | Mean tok/s |
|---|---|---|---|---|---|---|---|
| i3s-balanced | 7 | 7 | 100.00% | 46.04 s | 43.29 s | 73.44 s | 1.64 tok/s |
| i3s-coding | 7 | 7 | 100.00% | 54.80 s | 54.63 s | 76.66 s | 1.53 tok/s |
| i3s-diagrams | 6 | 6 | 100.00% | 51.40 s | 51.48 s | 64.78 s | 1.38 tok/s |
| i3s-fast | 7 | 7 | 100.00% | 19.59 s | 19.43 s | 32.66 s | 10.82 tok/s |

## Concurrency comparison

| Concurrency | Requests | Successful | Success rate | Mean latency | p50 | p95 | Mean tok/s |
|---|---|---|---|---|---|---|---|
| 1 | 20 | 20 | 100.00% | 41.20 s | 36.09 s | 74.32 s | 4.34 tok/s |
| 2 | 7 | 7 | 100.00% | 46.78 s | 49.75 s | 73.96 s | 2.78 tok/s |

## Fastest successful requests

| Alias | Scenario | Latency | Prompt words |
|---|---|---|---|
| i3s-fast | short | 1.39 s | 18 |
| i3s-fast | short | 15.00 s | 18 |
| i3s-fast | short | 15.72 s | 18 |
| i3s-fast | long | 19.43 s | 412 |
| i3s-fast | medium | 20.45 s | 29 |
| i3s-coding | short | 27.08 s | 18 |
| i3s-balanced | short | 27.26 s | 18 |
| i3s-balanced | short | 27.45 s | 18 |
| i3s-balanced | long | 28.73 s | 412 |
| i3s-coding | short | 30.58 s | 18 |

## Slowest successful requests

| Alias | Scenario | Latency | Prompt words |
|---|---|---|---|
| i3s-coding | medium | 77.19 s | 29 |
| i3s-coding | medium | 75.44 s | 29 |
| i3s-balanced | medium | 74.26 s | 29 |
| i3s-balanced | short | 71.55 s | 18 |
| i3s-coding | short | 70.68 s | 18 |
| i3s-diagrams | short | 66.44 s | 18 |
| i3s-diagrams | medium | 59.80 s | 29 |
| i3s-diagrams | long | 57.61 s | 412 |
| i3s-coding | short | 54.63 s | 18 |
| i3s-balanced | medium | 49.75 s | 29 |

## Resource observations

Largest observed per-request end-minus-start VRAM change: 8367.0 MiB. GPU samples are point-in-time snapshots and may miss peak utilisation. Largest observed RAM change: 917.4 MiB. CPU load and RAM values are also snapshots; use trends for capacity decisions.

## Evaluation observations

Language-switch flags: 0; fake tool/function JSON flags: 0; Mermaid-present flags: 0; refusal/warning flags: 0; truncation flags: 0. These are lightweight heuristics, not a safety certification or a complete quality assessment.

## Recommended serving limits

Start normal operation at one active generation per P100 and admit a second request only as queued or controlled concurrency. The current Ollama setting already limits loaded models to one and parallel work to two. Do not infer readiness for three or more simultaneous users from a quick run; rerun a representative bounded benchmark after any model, context, quantisation or gateway-profile change. Set user expectations for queueing and enforce request timeouts.

## Method and limitations

The benchmark uses the local OpenAI-compatible LiteLLM chat endpoint, fixed temperature 0, streaming when available, and no more than concurrency 3. Time to first token measures first streamed content received. Tokens/sec is completion tokens divided by full request duration, so it includes queueing, prompt work and model loading. Records append across runs; filter by run_id for a single run. Review response previews/full JSONL before sharing internally.
