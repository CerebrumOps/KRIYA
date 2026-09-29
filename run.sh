#!/bin/bash
# ==============================================================================
# KRIYA Sovereign AI Client Appliance — Daily Launcher
# ==============================================================================
# Starts the container appliance in the background, waits for service readiness,
# and automatically opens your browser to the KRIYA workbench.
# ==============================================================================

set -e

BOLD="\033[1m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[0;33m"
NC="\033[0m"

echo -e "${BOLD}${BLUE}========================================================================${NC}"
echo -e "${BOLD}${BLUE}  🚀 Starting KRIYA Sovereign AI Client Workbench${NC}"
echo -e "${BOLD}${BLUE}========================================================================${NC}"

# Ensure host-bridge shared directory exists
mkdir -p "$HOME/kriya-shared"

# Start container appliance in background
echo -e "\n  📦 Launching containerized environment..."
docker compose up -d

# Wait for frontend UI readiness on port 3000
echo -n "  ⏳ Waiting for Workbench interface..."
MAX_ATTEMPTS=40
READY=false

for i in $(seq 1 $MAX_ATTEMPTS); do
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 | grep -q "200"; then
        READY=true
        break
    fi
    echo -n "."
    sleep 0.5
done
echo ""

if [ "$READY" = true ]; then
    echo -e "  ${GREEN}✓${NC} Workbench is active and ready!"
else
    echo -e "  ${YELLOW}!${NC} Starting up, will open browser momentarily..."
fi

# Automatically open default browser
URL="http://localhost:3000"
echo -e "  🌐 Opening ${BOLD}$URL${NC} in your browser..."

if command -v xdg-open &> /dev/null; then
    xdg-open "$URL" > /dev/null 2>&1 &
elif command -v open &> /dev/null; then
    open "$URL" > /dev/null 2>&1 &
elif command -v sensible-browser &> /dev/null; then
    sensible-browser "$URL" > /dev/null 2>&1 &
elif [ -n "$WSL_DISTRO_NAME" ]; then
    cmd.exe /c start "$URL" > /dev/null 2>&1 &
fi

echo -e "\n${BOLD}${GREEN}========================================================================${NC}"
echo -e "${BOLD}${GREEN}  ✨ KRIYA Workbench is open in your browser!${NC}"
echo -e "${BOLD}${GREEN}========================================================================${NC}"
echo -e "  • Web UI:             ${BOLD}http://localhost:3000${NC}"
echo -e "  • Local Agent API:    ${BOLD}http://localhost:5001${NC}"
echo -e "  • Shared Host Bridge: ${BOLD}$HOME/kriya-shared${NC}"
echo -e "  ----------------------------------------------------------------------"
echo -e "  Press ${BOLD}Ctrl+C${NC} to stop viewing logs (the app keeps running)."
echo -e "  To stop the appliance completely, run: ${BOLD}./stop.sh${NC}"
echo -e "========================================================================\n"

# Stream live appliance logs to terminal
docker compose logs -f kriya-client
