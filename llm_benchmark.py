#!/usr/bin/env python3
"""Bounded local LiteLLM benchmark. Default: c=1,2; --concurrency-3 adds c=3; --quick is four c=1 requests."""
import argparse, csv, datetime, fcntl, json, os, re, sys, threading, time, uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler

from ops_common import ROOT, api_key, gateway, redact

ALIASES = ("i3s-fast", "i3s-balanced", "i3s-coding", "i3s-diagrams")
FIELDS = "timestamp run_id model_alias scenario test_name prompt_characters prompt_words context_size_setting max_tokens_setting concurrency success http_api_error total_latency_seconds time_to_first_token_seconds tokens_per_second completion_tokens prompt_tokens total_tokens response_characters response_words response_preview looks_truncated switched_language contains_fake_tool_json includes_mermaid_expected refused_warned_expected gpu_vram_mib_before gpu_vram_mib_after gpu_util_percent_before gpu_util_percent_after ram_used_mib_before ram_used_mib_after cpu_load_1m_before cpu_load_1m_after finish_reason".split()
SCENARIOS = {
    "short": ("Reply in English in two concise sentences: explain why a local AI service should have a health check.", "en", "general"),
    "medium": ("Explain in English, in about 100 words, how Open WebUI, LiteLLM, Ollama and a GPU cooperate to answer a chat request. State one performance constraint and one operational check.", "en", "technical"),
    "long": ("You are assessing a local AI service. " + "Summarise this operational note accurately and in English: requests pass through a web interface and a local gateway to a model server. GPU memory limits loaded-model capacity, concurrent requests may queue, logs help diagnose errors, and important answers require review. " * 10 + "Give a concise five-bullet summary.", "en", "context"),
}

def system_sample():
    out = {"gpu_vram_mib": "", "gpu_util_percent": "", "ram_used_mib": "", "cpu_load_1m": ""}
    try:
        import subprocess
        p = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,utilization.gpu", "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=8)
        if p.returncode == 0 and p.stdout.strip():
            vals = [x.strip() for x in p.stdout.splitlines()[0].split(",")]
            out["gpu_vram_mib"], out["gpu_util_percent"] = vals[:2]
    except Exception: pass
    try:
        mem = open("/proc/meminfo").read(); total = int(re.search(r"MemTotal:\s+(\d+)", mem).group(1)); avail = int(re.search(r"MemAvailable:\s+(\d+)", mem).group(1))
        out["ram_used_mib"] = round((total - avail) / 1024, 1)
        out["cpu_load_1m"] = round(os.getloadavg()[0], 2)
    except Exception: pass
    return out

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs): return None

def stream_completion(payload, timeout):
    """Returns text, usage, finish reason and TTFT. Uses SSE only; credentials never enter outputs."""
    base = os.environ.get("LITELLM_BASE_URL", "http://127.0.0.1:4000/v1").rstrip("/")
    parsed = urlparse(base)
    if parsed.scheme != "http" or parsed.hostname not in ("localhost", "127.0.0.1", "::1") or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise RuntimeError("LITELLM_BASE_URL must be a credential-free local HTTP endpoint")
    payload = dict(payload, stream=True, stream_options={"include_usage": True})
    req = Request(base + "/chat/completions", data=json.dumps(payload).encode(), headers={"Authorization": "Bearer " + api_key(), "Content-Type": "application/json", "Accept": "text/event-stream"})
    opener = build_opener(ProxyHandler({}), NoRedirect())
    started = time.monotonic(); first = None; chunks = []; usage = {}; finish = ""
    with opener.open(req, timeout=timeout) as response:
        for raw in response:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"): continue
            data = line[5:].strip()
            if data == "[DONE]": break
            event = json.loads(data)
            usage.update(event.get("usage") or {})
            for choice in event.get("choices", []):
                content = (choice.get("delta") or {}).get("content")
                if content:
                    if first is None: first = time.monotonic() - started
                    chunks.append(content)
                finish = choice.get("finish_reason") or finish
    return "".join(chunks), usage, finish, first

def flags(text, expected_lang, expected_mermaid=False, expected_refusal=False):
    lower = text.lower(); prose = re.sub(r"```.*?```", "", lower, flags=re.S); words = re.findall(r"\b[\wÀ-ÿ]+\b", prose)
    english = sum(w in {"the","and","is","are","you","your","cannot","with","for","that","this"} for w in words)
    portuguese = sum(w in {"o","a","de","e","não","que","para","com","ficheiro","ecrã"} for w in words)
    switched = portuguese >= 3 and portuguese > english * 1.5 if expected_lang == "en" else english >= 3 and english > portuguese * 1.5
    fake = bool(re.search(r'"(?:tool_calls|function_call|arguments|recipient_name)"\s*:|<tool_call>|\{\s*"(?:name|function|tool)"\s*:', text))
    return {"looks_truncated": bool(text.count("```") % 2), "switched_language": switched, "contains_fake_tool_json": fake, "includes_mermaid_expected": bool(re.search(r"```mermaid\s*\n", text, re.I)) if expected_mermaid else "", "refused_warned_expected": bool(re.search(r"\b(cannot|can't|unable|sorry|refuse|won't|no access|não posso|não tenho)\b", lower)) if expected_refusal else ""}

def one_request(run_id, alias, scenario, prompt, language, max_tokens, concurrency, timeout):
    before = system_sample(); stamp = datetime.datetime.now(datetime.timezone.utc).isoformat(); started = time.monotonic()
    response = ""; usage = {}; finish = ""; ttft = None; error = ""
    try:
        response, usage, finish, ttft = stream_completion({"model": alias, "messages": [{"role":"system","content":"You are evaluated offline. No tools or internet are available."},{"role":"user","content":prompt}], "temperature":0, "max_tokens":max_tokens}, timeout)
        if not response.strip(): error = "Empty response"
    except (HTTPError, URLError, TimeoutError, ValueError, OSError, json.JSONDecodeError) as exc: error = redact(exc)
    elapsed = time.monotonic() - started; after = system_sample(); response = redact(response)
    completion = usage.get("completion_tokens", ""); prompt_tokens = usage.get("prompt_tokens", ""); total = usage.get("total_tokens", "")
    f = flags(response, language)
    return dict(timestamp=stamp, run_id=run_id, model_alias=alias, scenario="single_user_latency" if concurrency == 1 else "concurrent_users", test_name=scenario, prompt_characters=len(prompt), prompt_words=len(re.findall(r"\S+", prompt)), context_size_setting="not_set", max_tokens_setting=max_tokens, concurrency=concurrency, success=not error, http_api_error=error, total_latency_seconds=round(elapsed,3), time_to_first_token_seconds=round(ttft,3) if ttft is not None else "", tokens_per_second=round(completion/elapsed,2) if isinstance(completion,(int,float)) and completion else "", completion_tokens=completion, prompt_tokens=prompt_tokens, total_tokens=total, response_characters=len(response), response_words=len(re.findall(r"\S+",response)), response_preview=response[:500], gpu_vram_mib_before=before["gpu_vram_mib"], gpu_vram_mib_after=after["gpu_vram_mib"], gpu_util_percent_before=before["gpu_util_percent"], gpu_util_percent_after=after["gpu_util_percent"], ram_used_mib_before=before["ram_used_mib"], ram_used_mib_after=after["ram_used_mib"], cpu_load_1m_before=before["cpu_load_1m"], cpu_load_1m_after=after["cpu_load_1m"], finish_reason=finish, **f)

def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument("--quick", action="store_true", help="one short single-user request per alias"); ap.add_argument("--concurrency-3", action="store_true", help="include bounded concurrency 3; never higher"); ap.add_argument("--timeout", type=float, default=180); ap.add_argument("--max-tokens", type=int, default=256); ap.add_argument("--models", nargs="+", choices=ALIASES, default=list(ALIASES)); args = ap.parse_args()
    if args.timeout <= 0 or args.max_tokens <= 0: ap.error("timeout and max-tokens must be positive")
    lock = (ROOT / ".llm_benchmark.lock").open("w")
    try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError: print("Another benchmark is running.", file=sys.stderr); return 2
    try: available = {x["id"] for x in gateway("/models", timeout=20)["data"]}
    except Exception as exc: print("Gateway preflight failed: " + redact(exc), file=sys.stderr); return 2
    if missing := set(args.models) - available: print("Unavailable aliases: " + ", ".join(sorted(missing)), file=sys.stderr); return 2
    csv_path = ROOT / "llm_benchmark_results.csv"; jsonl_path = ROOT / "llm_benchmark_responses.jsonl"
    if csv_path.exists() and csv_path.stat().st_size:
        with csv_path.open(newline="") as f:
            if next(csv.reader(f)) != FIELDS: print("Existing CSV schema differs; archive it before running.", file=sys.stderr); return 2
    run_id = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    plans = [(1, "short")] if args.quick else [(c, s) for c in ([1,2] + ([3] if args.concurrency_3 else [])) for s in SCENARIOS]
    rows = []
    with csv_path.open("a", newline="") as cf, jsonl_path.open("a") as jf:
        writer = csv.DictWriter(cf, fieldnames=FIELDS)
        if cf.tell() == 0: writer.writeheader()
        for concurrency, scenario in plans:
            prompt, language, _ = SCENARIOS[scenario]; jobs = [(alias, scenario, prompt, language) for alias in args.models]
            print(f"{scenario}, concurrency {concurrency}: {len(jobs)} request(s)", flush=True)
            with ThreadPoolExecutor(max_workers=concurrency) as pool:
                futures = [pool.submit(one_request, run_id, alias, scenario, p, lang, args.max_tokens, concurrency, args.timeout) for alias, scenario, p, lang in jobs]
                for future in as_completed(futures):
                    row = future.result(); writer.writerow(row); cf.flush(); jf.write(json.dumps(row, ensure_ascii=False) + "\n"); jf.flush(); rows.append(row)
                    print(f"  {row['model_alias']}: {'OK' if row['success'] else 'FAILED'} {row['total_latency_seconds']}s", flush=True)
    failed = sum(not r["success"] for r in rows); print(f"Run {run_id}: {len(rows)-failed}/{len(rows)} successful. Results appended to {csv_path.name}.")
    return 1 if failed else 0
if __name__ == "__main__":
    try: sys.exit(main())
    except KeyboardInterrupt: print("Interrupted; completed records are preserved.", file=sys.stderr); sys.exit(130)
