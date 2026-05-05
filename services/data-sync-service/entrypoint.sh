#!/bin/sh
# Dev-friendly entrypoint: ensure Python deps are present before starting
set -e

echo "[entrypoint] Checking Python dependencies..."
python - <<'PY'
try:
    import fastapi  # noqa: F401
    print('[entrypoint] fastapi already installed')
except Exception:
    raise SystemExit(2)
PY

if [ "$?" -eq 2 ]; then
    echo "[entrypoint] fastapi missing — installing requirements..."
    pip install --no-cache-dir -r /app/requirements.txt || true
fi

echo "[entrypoint] Starting service: $@"
exec "$@"
