#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🚀 Starting Claudable Development Environment${NC}"
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$ROOT_DIR"

echo -e "${YELLOW}📦 Installing dependencies...${NC}"
npm install

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to install dependencies${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}⚙️  Setting up environment...${NC}"
node scripts/setup-env.js

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to setup environment${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}🐍 Setting up Python virtual environment...${NC}"
node scripts/setup-venv.js

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to setup Python virtual environment${NC}"
    exit 1
fi

# Load environment variables from .env file
if [ -f "$ROOT_DIR/.env" ]; then
    export $(cat "$ROOT_DIR/.env" | grep -v '^#' | xargs)
fi

API_PORT=${API_PORT:-8080}
WEB_PORT=${WEB_PORT:-3000}

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo -e "${YELLOW}🔧 Starting servers...${NC}"
echo -e "   API: http://localhost:${API_PORT}"
echo -e "   Web: http://localhost:${WEB_PORT}"
echo ""

cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down servers...${NC}"
    kill $(jobs -p) 2>/dev/null || true
    wait
    echo -e "${GREEN}👋 Goodbye!${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

API_PORT=$API_PORT WEB_PORT=$WEB_PORT node scripts/run-api.js &
API_PID=$!

sleep 2

API_PORT=$API_PORT WEB_PORT=$WEB_PORT node scripts/run-web.js &
WEB_PID=$!

echo ""
echo -e "${GREEN}✨ All services are running!${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

wait $API_PID $WEB_PID