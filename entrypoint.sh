#!/bin/bash
# ==============================================================================
# KRIYA Client Appliance — Container Entrypoint
# ==============================================================================
# Initializes local SQLite storage, per-chat workspace hierarchy, starts the
# local FastAPI agent harness on port 5001, and serves the UI on port 3000.
# ==============================================================================

set -e

echo "========================================================================"
echo "  🚀 Starting KRIYA Sovereign AI Appliance"
echo "========================================================================"

# 1. Ensure required local directories exist
mkdir -p /app/data /app/workspace/chats /host-bridge

# 2. Initialize local SQLite tables
echo "  📦 Initializing local SQLite database at /app/data/kriya_local.db..."
python3 -c "import asyncio; from agent.database.sqlite_db import init_sqlite_db; asyncio.run(init_sqlite_db()); print('  ✓ Local SQLite initialized.')"

# 3. Graceful shutdown handler
cleanup() {
    echo -e "\n  🛑 Stopping KRIYA services..."
    if [ -n "$UVICORN_PID" ]; then
        kill "$UVICORN_PID" 2>/dev/null || true
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi
    exit 0
}
trap cleanup SIGINT SIGTERM

# 4. Start local agent FastAPI server on port 5001
echo "  ⚙️  Starting KRIYA Agent API on http://0.0.0.0:5001..."
uvicorn agent.main:app --host 0.0.0.0 --port 5001 &
UVICORN_PID=$!

# Wait for local agent API to become healthy
echo "  ⏳ Waiting for Agent API readiness..."
for i in {1..30}; do
    if curl -s http://127.0.0.1:5001/health >/dev/null 2>&1; then
        echo "  ✓ Agent API is ready."
        break
    fi
    sleep 0.5
done

# 5. Start frontend UI server on port 3000
echo "  🌐 Starting KRIYA Web UI on http://0.0.0.0:3000..."
cd /app/frontend
npm run preview -- --host 0.0.0.0 --port 3000 &
FRONTEND_PID=$!

echo "========================================================================"
echo "  ✨ KRIYA Appliance is fully operational!"
echo "  💻 UI URL:       http://localhost:3000"
echo "  🤖 Agent API:    http://localhost:5001"
echo "========================================================================"

# Wait on background processes
wait "$FRONTEND_PID" "$UVICORN_PID"
