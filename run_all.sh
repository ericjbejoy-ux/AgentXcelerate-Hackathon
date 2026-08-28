#!/usr/bin/env bash
# Kill anything on the AgentXcelerate ports, then start all 4 services.
# Ports: 8001 (supplier/logistics), 8101 (main app), 8102 (legacy), 5173 (frontend)
set -euo pipefail

cd "$(dirname "$0")"

PORTS=(8001 8101 8102 5173)

echo "==> Killing anything on ports: ${PORTS[*]}"
for p in "${PORTS[@]}"; do
    pids=$(ss -tlnp 2>/dev/null | awk -v p=":$p " '$0 ~ p { for (i=1;i<=NF;i++) if ($i ~ /pid=/) { gsub(/[^0-9]/,"",$i); print $i } }' | sort -u)
    if [ -n "$pids" ]; then
        for pid in $pids; do
            echo "    killing PID $pid on port $p"
            kill "$pid" 2>/dev/null || true
        done
    else
        echo "    port $p already free"
    fi
done

sleep 1

source .venv/bin/activate

echo "==> Starting supplier & logistics on 8001"
nohup uvicorn mocks.supplier_server:app --host 0.0.0.0 --port 8001 > /tmp/supplier_8001.log 2>&1 &

echo "==> Starting main SCM app on 8101"
nohup uvicorn main:app --host 0.0.0.0 --port 8101 > /tmp/main_8101.log 2>&1 &

echo "==> Starting legacy optimizer on 8102"
nohup uvicorn app:app --host 0.0.0.0 --port 8102 > /tmp/app_8102.log 2>&1 &

echo "==> Starting React frontend on 5173"
(cd frontend-react && nohup npm run dev > /tmp/frontend_5173.log 2>&1 &)

sleep 4

echo
echo "==> Health checks:"
curl -s -m 5 http://127.0.0.1:8001/health && echo "  <- supplier OK" || echo "  <- supplier FAILED (see /tmp/supplier_8001.log)"
curl -s -m 5 http://127.0.0.1:8101/api/v1/health && echo "  <- main OK" || echo "  <- main FAILED (see /tmp/main_8101.log)"
curl -s -m 5 -o /dev/null -w 'HTTP %{http_code}' http://127.0.0.1:8102/ && echo "  <- legacy OK" || echo "  <- legacy FAILED (see /tmp/app_8102.log)"
curl -s -m 5 -o /dev/null -w 'HTTP %{http_code}' http://localhost:5173/ && echo "  <- frontend OK" || echo "  <- frontend FAILED (see /tmp/frontend_5173.log)"

echo
echo "Done. Open http://localhost:5173"
