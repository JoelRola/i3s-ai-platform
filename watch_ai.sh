#!/usr/bin/env bash
set -eu
OPS_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ "${1:-}" == "--once" ]]; then
  exec python3 "$OPS_DIR/status_report.py" --watch
fi
exec watch -n 2 -x python3 "$OPS_DIR/status_report.py" --watch
