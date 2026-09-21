#!/usr/bin/env bash
set -euo pipefail

out_dir=/home/jorola/i3s_ai_ops/gpu_split_upgrade
csv="$out_dir/qwen35_9b_benchmark.csv"
txt="$out_dir/qwen35_9b_benchmark.txt"
printf 'run,prompt_class,wall_latency_s,load_s,prompt_eval_s,eval_s,ttft_approx_s,prompt_tokens,completion_tokens,generation_tok_s,a100_mem_mib,a100_util_pct,p100_mem_mib,p100_util_pct,cpu_pct,ram_used_mib\n' > "$csv"

run_case() {
  local run="$1" cls="$2" prompt="$3" predicts="$4"
  local response sample start end wall cpu ram
  response="$(mktemp /tmp/qwen35-response.XXXXXX)"
  start="$(date +%s%N)"
  curl --fail --silent --show-error http://127.0.0.1:11434/api/generate \
    -H 'Content-Type: application/json' \
    -d "$(jq -nc --arg model 'qwen3.5:9b' --arg prompt "$prompt" --argjson n "$predicts" '{model:$model,prompt:$prompt,stream:false,options:{num_predict:$n,temperature:0.2}}')" > "$response" &
  local pid=$!
  sleep 1
  sample="$(nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader,nounits | tr '\n' ';')"
  wait "$pid"
  end="$(date +%s%N)"
  wall="$(awk -v s="$start" -v e="$end" 'BEGIN { printf "%.6f", (e-s)/1000000000 }')"
  cpu="$(ps -C ollama -o %cpu= | awk '{s+=$1} END {printf "%.1f",s+0}')"
  ram="$(free -m | awk '/Mem:/ {print $3}')"
  jq -r --arg run "$run" --arg cls "$cls" --arg wall "$wall" --arg sample "$sample" --arg cpu "$cpu" --arg ram "$ram" '
    ($sample | split(";") | map(select(length>0) | split(",") | map(gsub(" ";"")))) as $g |
    [ $run, $cls, $wall,
      (.load_duration/1e9), (.prompt_eval_duration/1e9), (.eval_duration/1e9),
      ((.load_duration+.prompt_eval_duration)/1e9), .prompt_eval_count, .eval_count,
      (if .eval_duration > 0 then .eval_count/(.eval_duration/1e9) else 0 end),
      $g[1][0], $g[1][1], $g[0][0], $g[0][1], $cpu, $ram ] | @csv' "$response" >> "$csv"
  rm -f "$response"
}

run_case cold normal 'What are three practical ways to improve a team handoff?' 120
run_case warm1 technical 'Explain why GPU memory bandwidth matters for transformer inference.' 140
run_case warm2 coding 'Write a Python function that retries an HTTP operation with exponential backoff.' 160
run_case warm3 synthesis 'Synthesize this: a project has limited budget, high reliability needs, and a two-week deadline. Give a prioritized plan.' 160
run_case warm4 long_context "$(printf 'Background: the system serves local models, separates inference from embedding, and stores documents for retrieval. %.0s' {1..80}) Summarize the architectural tradeoffs in five points." 180
run_case safety tool_safety 'Tell me a really complex folk story.' 220

{
  echo 'Model: qwen3.5:9b'
  echo 'TTFT approximation is load_duration + prompt_eval_duration from Ollama timing fields; generation tok/s is eval_count / eval_duration, not wall-clock throughput.'
  echo
  column -s, -t < "$csv"
} > "$txt"
