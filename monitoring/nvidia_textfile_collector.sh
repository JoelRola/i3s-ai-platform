#!/usr/bin/env bash
set -euo pipefail

output_dir=/home/jorola/i3s_ai_ops/monitoring/node-textfile
output_file="$output_dir/nvidia_gpu.prom"
temporary_file="$output_dir/.nvidia_gpu.prom.$$"

mkdir -p "$output_dir"

{
  echo '# HELP nvidia_gpu_utilization_percent GPU utilization percentage.'
  echo '# TYPE nvidia_gpu_utilization_percent gauge'
  echo '# HELP nvidia_gpu_memory_used_bytes GPU memory in use in bytes.'
  echo '# TYPE nvidia_gpu_memory_used_bytes gauge'
  echo '# HELP nvidia_gpu_memory_total_bytes Total GPU memory in bytes.'
  echo '# TYPE nvidia_gpu_memory_total_bytes gauge'
  echo '# HELP nvidia_gpu_temperature_celsius GPU temperature in degrees Celsius.'
  echo '# TYPE nvidia_gpu_temperature_celsius gauge'
  echo '# HELP nvidia_gpu_power_watts GPU power draw in watts.'
  echo '# TYPE nvidia_gpu_power_watts gauge'
  echo '# HELP i3s_service_up Private I3S service endpoint or daemon health (1=reachable/active).'
  echo '# TYPE i3s_service_up gauge'

  nvidia-smi --query-gpu=index,name,uuid,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw \
    --format=csv,noheader,nounits | while IFS=, read -r index name uuid utilization memory_used memory_total temperature power; do
      name=$(echo "$name" | xargs)
      uuid=$(echo "$uuid" | xargs)
      utilization=$(echo "$utilization" | xargs)
      memory_used=$(echo "$memory_used" | xargs)
      memory_total=$(echo "$memory_total" | xargs)
      temperature=$(echo "$temperature" | xargs)
      power=$(echo "$power" | xargs)
      labels="gpu_index=\"$index\",gpu_name=\"$name\",uuid=\"$uuid\""
      printf 'nvidia_gpu_utilization_percent{%s} %s\n' "$labels" "$utilization"
      printf 'nvidia_gpu_memory_used_bytes{%s} %.0f\n' "$labels" "$(awk -v m="$memory_used" 'BEGIN { print m * 1048576 }')"
      printf 'nvidia_gpu_memory_total_bytes{%s} %.0f\n' "$labels" "$(awk -v m="$memory_total" 'BEGIN { print m * 1048576 }')"
      printf 'nvidia_gpu_temperature_celsius{%s} %s\n' "$labels" "$temperature"
      printf 'nvidia_gpu_power_watts{%s} %s\n' "$labels" "$power"
    done

  service_up() {
    local name="$1" url="$2" status
    status=$(curl --silent --output /dev/null --write-out '%{http_code}' --max-time 3 "$url" || true)
    if [[ "$status" =~ ^[1-4][0-9][0-9]$ ]]; then
      printf 'i3s_service_up{service="%s"} 1\n' "$name"
    else
      printf 'i3s_service_up{service="%s"} 0\n' "$name"
    fi
  }
  systemctl is-active --quiet ollama && echo 'i3s_service_up{service="main_ollama"} 1' || echo 'i3s_service_up{service="main_ollama"} 0'
  systemctl is-active --quiet ollama-embed && echo 'i3s_service_up{service="embedding_ollama"} 1' || echo 'i3s_service_up{service="embedding_ollama"} 0'
  service_up open_webui http://127.0.0.1:8080/health
  service_up litellm http://127.0.0.1:4000/health
  service_up tika http://127.0.0.1:9998/tika
  service_up prometheus http://127.0.0.1:9090/-/ready
  service_up grafana http://127.0.0.1:3001/api/health
} > "$temporary_file"

# LiteLLM is intentionally loopback-only. Re-export only its authenticated,
# actually exposed Prometheus metrics via the already private node-exporter.
metrics_token=$(awk '/^[[:space:]]*master_key:/{print $2; exit}' /opt/litellm/config.yaml)
curl --fail --silent --show-error --location --max-time 5 \
  -H "Authorization: Bearer $metrics_token" http://127.0.0.1:4000/metrics >> "$temporary_file" || true

mv "$temporary_file" "$output_file"
