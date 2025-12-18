#!/bin/bash
# Start the git proxy server

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Warning: .env file not found. Using defaults."
fi

# Check for required environment variables
if [ -z "$PROXY_SECRET_KEY" ]; then
    echo "Error: PROXY_SECRET_KEY not set"
    echo "Please create .env file from .env.example"
    exit 1
fi

# Start server
echo "Starting Git Proxy Server..."
echo "Workspace: ${GIT_WORKSPACE:-~/git-proxy-workspace}"
echo "Port: ${PORT:-8443}"

cd "$(dirname "$0")/.."
python3 server/proxy_server.py
