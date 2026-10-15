# ==============================================================================
# KRIYA Sovereign AI Client Appliance — Dockerfile (Ubuntu 24.04 Server)
# ==============================================================================
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Kolkata
ENV PYTHONUNBUFFERED=1
ENV KRIYA_CONTAINER=1

WORKDIR /app

# Ensure root access inside container environment
USER root

# 1. Install Ubuntu system packages, Python 3, network tools, build essentials, and sudo
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    wget \
    git \
    sudo \
    procps \
    net-tools \
    iptables \
    iproute2 \
    build-essential \
    ca-certificates \
    gnupg \
    tesseract-ocr \
    poppler-utils \
    && echo "root ALL=(ALL:ALL) NOPASSWD: ALL" >> /etc/sudoers \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Node.js LTS (v22.x)
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# 3. Setup isolated Python virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PYTHONPATH="/app"

# 4. Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Build Frontend UI
COPY frontend/package*.json ./frontend/
WORKDIR /app/frontend
RUN npm install
COPY frontend/ .
ENV VITE_AUTH_BACKEND_URL=http://localhost:5000
ENV VITE_BACKEND_URL=http://localhost:5001
RUN npm run build

# 6. Copy Agent Harness and Entrypoint
WORKDIR /app
COPY agent/ ./agent/
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# 7. Create volume mount points and per-chat directories
RUN mkdir -p /app/data /app/workspace/chats /host-bridge /host_shared

EXPOSE 3000 5001

USER root
ENTRYPOINT ["/app/entrypoint.sh"]
