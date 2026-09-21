#!/usr/bin/env bash
# Conservative observation only: never changes Funnel state.
set -euo pipefail
out_dir=/home/jorola/i3s_ai_ops/monitoring/node-textfile
state_dir=/home/jorola/i3s_ai_ops/monitoring/state
out="$out_dir/public_access.prom"; tmp="$out.$$"
mkdir -p "$out_dir" "$state_dir"

check_http() { # name URL; succeeds for any usable HTTP response, including auth redirects
  local name="$1" url="$2" response code latency ok prior count
  response=$(curl --silent --show-error --output /dev/null --max-time 12 --connect-timeout 5 --write-out '%{http_code} %{time_total}' "$url" 2>/dev/null || true)
  read -r code latency <<< "${response:-000 0}"
  [[ "$code" =~ ^[1-4][0-9][0-9]$ ]] && ok=1 || ok=0
  prior=$(cat "$state_dir/$name.failures" 2>/dev/null || echo 0)
  (( ok )) && count=0 || count=$((prior+1)); printf '%s\n' "$count" > "$state_dir/$name.failures"
  printf 'i3s_public_http_up{endpoint="%s"} %s\n' "$name" "$ok"
  printf 'i3s_public_http_status{endpoint="%s"} %s\n' "$name" "$code"
  printf 'i3s_public_http_latency_seconds{endpoint="%s"} %s\n' "$name" "$latency"
  printf 'i3s_public_consecutive_failures{endpoint="%s"} %s\n' "$name" "$count"
}
check_dns() {
  local answer ok prior count
  answer=$(dig @1.1.1.1 +time=4 +tries=1 +short brain2.tailcedd84.ts.net A 2>/dev/null || true)
  [[ -n "$answer" ]] && ok=1 || ok=0; prior=$(cat "$state_dir/dns.failures" 2>/dev/null || echo 0)
  (( ok )) && count=0 || count=$((prior+1)); printf '%s\n' "$count" > "$state_dir/dns.failures"
  printf 'i3s_public_dns_up{resolver="1.1.1.1",host="brain2.tailcedd84.ts.net"} %s\n' "$ok"
  printf 'i3s_public_consecutive_failures{endpoint="dns"} %s\n' "$count"
}
{
 echo '# HELP i3s_public_http_up Public endpoint HTTP availability.'; echo '# TYPE i3s_public_http_up gauge'
 echo '# HELP i3s_public_http_status Last public endpoint HTTP status.'; echo '# TYPE i3s_public_http_status gauge'
 echo '# HELP i3s_public_http_latency_seconds Public endpoint request latency.'; echo '# TYPE i3s_public_http_latency_seconds gauge'
 echo '# HELP i3s_public_dns_up External DNS resolution availability.'; echo '# TYPE i3s_public_dns_up gauge'
 echo '# HELP i3s_public_consecutive_failures Consecutive availability failures; automatic repair is intentionally disabled.'; echo '# TYPE i3s_public_consecutive_failures gauge'
 check_http local_openwebui http://127.0.0.1:8080/
 check_dns
 check_http public_openwebui https://brain2.tailcedd84.ts.net/
 check_http public_grafana https://brain2.tailcedd84.ts.net:8443/
} > "$tmp"
mv "$tmp" "$out"
