#!/usr/bin/env bash

# ==============================================================================
# SVARP Email Portal Backend Deployment Script
# Target Service Name: email-portal-be
# ==============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

BRANCH="${BRANCH:-dev}"

echo -e "${CYAN}========================================================================${NC}"
echo -e "${CYAN}                Deploying SVARP Email Portal Backend                    ${NC}"
echo -e "${CYAN}========================================================================${NC}"

# Navigate to backend directory where this script is located
cd "$(dirname "$0")"

# 1. Pull latest code from origin dev branch
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo -e "${YELLOW}➜ Pulling latest backend code (origin/${BRANCH})...${NC}"
    git fetch origin "$BRANCH" || true
    git checkout "$BRANCH" || true
    git pull origin "$BRANCH" || true
fi

# 2. Check and update Python dependencies in virtualenv
if [ -f "requirements.txt" ]; then
    if [ -d "venv" ]; then
        echo -e "${YELLOW}➜ Updating Python virtualenv dependencies...${NC}"
        ./venv/bin/pip install -r requirements.txt
    elif [ -d "../venv" ]; then
        echo -e "${YELLOW}➜ Updating Python virtualenv dependencies...${NC}"
        ../venv/bin/pip install -r requirements.txt
    else
        echo -e "${YELLOW}Warning: Virtual environment not found. Skipping dependency installation.${NC}"
    fi
fi

# 3. Apply database migrations using Alembic
if [ -f "./scripts/migrate.sh" ]; then
    echo -e "${YELLOW}➜ Running database migrations...${NC}"
    ./scripts/migrate.sh apply
elif [ -f "./migrate.sh" ]; then
    echo -e "${YELLOW}➜ Running database migrations...${NC}"
    ./migrate.sh apply
elif [ -f "alembic.ini" ]; then
    echo -e "${YELLOW}➜ Running database migrations via Alembic...${NC}"
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    alembic upgrade head || alembic stamp head || true
fi

# 4. Restart backend systemd service
echo -e "${YELLOW}➜ Restarting backend systemd service (email-portal-be)...${NC}"
sudo systemctl restart email-portal-be

echo -e "${GREEN}========================================================================${NC}"
echo -e "${GREEN}✓ Email Portal Backend deployment completed successfully!                ${NC}"
echo -e "${GREEN}========================================================================${NC}"
