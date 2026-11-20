#!/bin/sh
set -eu

memegen=http://127.0.0.1:5001
attempt=1
echo "[Startup] waiting for Memegen at $memegen/test"
until curl --noproxy '*' --fail --silent --max-time 2 "$memegen/test" >/dev/null; do
    if [ "$attempt" -ge 30 ]; then
        echo '[Startup] Memegen readiness wait timed out' >&2
        exit 1
    fi
    attempt=$((attempt + 1))
    sleep 2
done
echo '[Startup] Memegen is ready'

if [ "${MEMEGEN_PREWARM_ENABLED:-1}" = 1 ]; then
    echo '[Startup] prewarming Memegen'
    if curl --noproxy '*' --fail --silent --max-time 30 "$memegen/images/fry/warmup/_.jpg" >/dev/null; then
        echo '[Startup] Memegen prewarm succeeded'
    else
        echo '[Startup] Memegen prewarm failed' >&2
    fi
fi

exec gunicorn --bind 0.0.0.0:8080 --worker-tmp-dir /tmp \
    --workers "${GUNICORN_WORKERS:-1}" --threads "${GUNICORN_THREADS:-2}" \
    --timeout "${GUNICORN_TIMEOUT:-180}" --access-logfile - --error-logfile - \
    ddbmeme.wsgi:application
