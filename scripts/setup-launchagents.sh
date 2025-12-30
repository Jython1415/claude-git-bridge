#!/bin/bash
#
# Setup LaunchAgents for Credential Proxy Servers
#
# This script configures macOS to automatically start both the Flask proxy server
# and MCP server when you log in. Run once to set up, then forget about it.
#
# Usage:
#   ./scripts/setup-launchagents.sh
#
# To check status:
#   launchctl list | grep joshuashew
#
# To manually stop/start:
#   launchctl stop com.joshuashew.credential-proxy
#   launchctl start com.joshuashew.credential-proxy
#
# To uninstall:
#   launchctl unload ~/Library/LaunchAgents/com.joshuashew.credential-proxy.plist
#   launchctl unload ~/Library/LaunchAgents/com.joshuashew.mcp-server.plist
#   rm ~/Library/LaunchAgents/com.joshuashew.credential-proxy.plist
#   rm ~/Library/LaunchAgents/com.joshuashew.mcp-server.plist

set -e

# Configuration
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
LOGS_DIR="$HOME/Library/Logs"

# Find uv binary
UV_BIN=$(which uv 2>/dev/null || echo "$HOME/.local/bin/uv")
if [ ! -x "$UV_BIN" ]; then
    echo "Error: uv not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "Setting up LaunchAgents for Credential Proxy..."
echo "Project directory: $PROJECT_DIR"
echo "uv binary: $UV_BIN"
echo ""

# Ensure .venv exists and dependencies are installed
echo "Syncing dependencies..."
(cd "$PROJECT_DIR" && "$UV_BIN" sync)
echo ""

# Ensure LaunchAgents directory exists
mkdir -p "$LAUNCH_AGENTS_DIR"

# --- Flask Credential Proxy Server ---

PROXY_PLIST="$LAUNCH_AGENTS_DIR/com.joshuashew.credential-proxy.plist"
PROXY_LABEL="com.joshuashew.credential-proxy"

# Unload existing if present
if launchctl list | grep -q "$PROXY_LABEL" 2>/dev/null; then
    echo "Stopping existing credential proxy..."
    launchctl unload "$PROXY_PLIST" 2>/dev/null || true
fi

echo "Creating $PROXY_PLIST..."
cat > "$PROXY_PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$PROXY_LABEL</string>

    <key>ProgramArguments</key>
    <array>
        <string>$UV_BIN</string>
        <string>run</string>
        <string>--frozen</string>
        <string>python</string>
        <string>$PROJECT_DIR/server/proxy_server.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>$LOGS_DIR/credential-proxy.log</string>

    <key>StandardErrorPath</key>
    <string>$LOGS_DIR/credential-proxy-error.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.local/bin</string>
    </dict>
</dict>
</plist>
EOF

echo "Loading credential proxy LaunchAgent..."
launchctl load "$PROXY_PLIST"

# --- MCP Server ---

MCP_PLIST="$LAUNCH_AGENTS_DIR/com.joshuashew.mcp-server.plist"
MCP_LABEL="com.joshuashew.mcp-server"

# Unload existing if present
if launchctl list | grep -q "$MCP_LABEL" 2>/dev/null; then
    echo "Stopping existing MCP server..."
    launchctl unload "$MCP_PLIST" 2>/dev/null || true
fi

echo "Creating $MCP_PLIST..."
cat > "$MCP_PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$MCP_LABEL</string>

    <key>ProgramArguments</key>
    <array>
        <string>$UV_BIN</string>
        <string>run</string>
        <string>--frozen</string>
        <string>python</string>
        <string>$PROJECT_DIR/mcp/server.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>$LOGS_DIR/mcp-server.log</string>

    <key>StandardErrorPath</key>
    <string>$LOGS_DIR/mcp-server-error.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.local/bin</string>
        <key>FLASK_URL</key>
        <string>http://localhost:8443</string>
    </dict>
</dict>
</plist>
EOF

echo "Loading MCP server LaunchAgent..."
launchctl load "$MCP_PLIST"

echo ""
echo "Done! Both servers are now configured to start on login."
echo ""
echo "Status:"
launchctl list | grep joshuashew || echo "  (services starting...)"
echo ""
echo "Logs:"
echo "  Proxy: $LOGS_DIR/credential-proxy.log"
echo "  MCP:   $LOGS_DIR/mcp-server.log"
echo ""
echo "Tailscale Funnel (run if not already configured):"
echo "  tailscale serve --bg --https=8443 http://127.0.0.1:8443"
echo "  tailscale serve --bg --https=8001 http://127.0.0.1:8001"
echo "  tailscale funnel 8443"
echo "  tailscale funnel 8001"
