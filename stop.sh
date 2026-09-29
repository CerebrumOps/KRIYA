#!/bin/bash
# ==============================================================================
# KRIYA Sovereign AI Client Appliance — Shutdown Script
# ==============================================================================
# Gracefully stops the container appliance and preserves persistent storage.
# ==============================================================================

set -e

BOLD="\033[1m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
NC="\033[0m"

echo -e "${BOLD}${BLUE}Stopping KRIYA Sovereign AI Client Appliance...${NC}"
docker compose down
echo -e "${BOLD}${GREEN}✓ KRIYA Appliance stopped cleanly. Your conversation data and workspace are preserved.${NC}"
