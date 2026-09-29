#!/bin/bash
# ==============================================================================
# KRIYA Sovereign AI Client Appliance — One-Click Setup Script
# ==============================================================================
# Verifies Docker runtime, creates local host directories, configures environment,
# and builds the self-contained container OS image.
# ==============================================================================

set -e

BOLD="\033[1m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NC="\033[0m"

echo -e "${BOLD}${BLUE}========================================================================${NC}"
echo -e "${BOLD}${BLUE}  🚀 KRIYA Sovereign AI Client Appliance — Automated Setup${NC}"
echo -e "${BOLD}${BLUE}========================================================================${NC}"

# 1. Check Docker installation
echo -e "\n${BOLD}[1/4] Checking system prerequisites...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed on this system.${NC}"
    echo -e "   Please install Docker Engine (https://docs.docker.com/engine/install/) and try again."
    exit 1
fi
echo -e "  ${GREEN}✓${NC} Docker CLI is available: $(docker --version)"

# Check Docker Compose (plugin or standalone)
if docker compose version &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} Docker Compose is available: $(docker compose version)"
elif command -v docker-compose &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} docker-compose is available: $(docker-compose --version)"
else
    echo -e "${RED}❌ Docker Compose is not installed.${NC}"
    echo -e "   Please install docker compose plugin and try again."
    exit 1
fi

# Check Docker daemon connectivity
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker daemon is not running or current user lacks permission.${NC}"
    echo -e "   Run 'sudo systemctl start docker' or ensure your user is in the 'docker' group."
    exit 1
fi
echo -e "  ${GREEN}✓${NC} Docker daemon is connected and active."

# 2. Setup Host Shared Bridge Directory
echo -e "\n${BOLD}[2/4] Setting up host bridge directory...${NC}"
HOST_SHARED_DIR="$HOME/kriya-shared"
mkdir -p "$HOST_SHARED_DIR"
echo -e "  ${GREEN}✓${NC} Shared host bridge ready at: ${BOLD}$HOST_SHARED_DIR${NC}"
echo -e "     (Files placed here are instantly accessible to your local agent)"

# 3. Setup Environment File
echo -e "\n${BOLD}[3/4] Checking environment configuration...${NC}"
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "  ${GREEN}✓${NC} Created .env from template (.env.example)"
    else
        echo -e "  ${YELLOW}!${NC} No .env.example found; skipping."
    fi
else
    echo -e "  ${GREEN}✓${NC} Existing .env detected."
fi

# 4. Build Client Container Appliance Image
echo -e "\n${BOLD}[4/4] Building KRIYA Client Appliance container image...${NC}"
echo -e "   (This may take 2-3 minutes during initial setup to bundle packages)"
docker compose build

echo -e "\n${BOLD}${GREEN}========================================================================${NC}"
echo -e "${BOLD}${GREEN}  ✅ Setup Complete! KRIYA Appliance is ready.${NC}"
echo -e "${BOLD}${GREEN}========================================================================${NC}"
echo -e "  To launch the workbench and open your browser, simply run:"
echo -e "     ${BOLD}${BLUE}./run.sh${NC}\n"
