#!/bin/bash
# Setup script for git proxy

set -e

echo "Git Proxy Setup"
echo "==============="

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip3 install -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.example .env

    # Generate secret key
    secret_key=$(openssl rand -hex 32)
    sed -i.bak "s/your-secret-key-here/$secret_key/g" .env
    rm .env.bak 2>/dev/null || true

    echo "✓ Generated secret key in .env"
    echo ""
    echo "IMPORTANT: Update GIT_PROXY_URL in .env with your ngrok or custom domain URL"
fi

# Create workspace directory
workspace="${GIT_WORKSPACE:-$HOME/git-proxy-workspace}"
mkdir -p "$workspace"
echo "✓ Created workspace: $workspace"

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update GIT_PROXY_URL in .env with your ngrok URL"
echo "2. Start the server: ./scripts/start_server.sh"
echo "3. In another terminal, start ngrok: ngrok http 8443"
echo "4. Copy the ngrok URL to .env"
