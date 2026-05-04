#!/usr/bin/env bash
# start-local.sh — legacy entry-point kept for compatibility.
# Delegates to manage.sh which provides start / stop / clean / seed / status.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/manage.sh" start "$@"
