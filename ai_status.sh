#!/usr/bin/env bash
set -eu
OPS_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$OPS_DIR/status_report.py"
