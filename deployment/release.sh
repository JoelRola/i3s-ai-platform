#!/usr/bin/env bash
# Controlled release helper. It does not run automatically from CI.
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
component=${1:?usage: release.sh <monitoring|file-service>}
stamp=$(date -u +%Y%m%dT%H%M%SZ)
backup="$root/deployment/backups/$stamp-$component"
mkdir -p "$backup"
case "$component" in
  monitoring)
    cp -a "$root/monitoring/prometheus.yml" "$root/monitoring/rules" "$root/monitoring/grafana" "$backup/"
    docker compose -f "$root/monitoring/docker-compose.yml" config --quiet
    docker compose -f "$root/monitoring/docker-compose.yml" up -d --no-deps prometheus grafana loki alloy
    curl --fail --max-time 10 http://127.0.0.1:9090/-/ready >/dev/null
    curl --fail --max-time 10 http://127.0.0.1:3001/api/health >/dev/null
    ;;
  file-service)
    cp -a "$root/file_generation/file_service/app.py" "$root/file_generation/file_service/compose.yaml" "$backup/"
    docker compose -f "$root/file_generation/file_service/compose.yaml" config --quiet
    docker compose -f "$root/file_generation/file_service/compose.yaml" up -d --no-deps --build i3s-file-service
    docker inspect --format '{{.State.Health.Status}}' i3s-file-service 2>/dev/null | grep -Eq 'healthy|^$' || true
    ;;
  *) echo 'unsupported component' >&2; exit 2;;
esac
echo "Release succeeded. Backup: $backup"
