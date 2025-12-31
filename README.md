# Claude Credential Proxy

Credential proxy and git bundle server for Claude.ai. Enables Claude to access APIs (Bluesky, GitHub, etc.) and clone/push git repos without exposing credentials.

## Features

- **Session-based authentication**: Time-limited sessions for secure API access
- **Transparent credential proxy**: Forward requests to APIs with credentials injected server-side
- **Git bundle operations**: Clone repos into Claude's environment, push changes back
- **MCP custom connector**: Claude.ai browser integration via Streamable HTTP

## Quick Start

### 1. Install Dependencies

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies (creates .venv automatically)
uv sync
```

### 2. Configure Credentials

```bash
# Copy example and add your API credentials
cp server/credentials.example.json server/credentials.json
# Edit server/credentials.json with your tokens
```

### 3. Start Servers (Auto-Start on Login)

```bash
# One-time setup - installs LaunchAgents for both servers
./scripts/setup-launchagents.sh
```

This starts:
- **Flask proxy** on port 8443 (sessions, proxy, git bundles)
- **MCP server** on port 10000 (custom connector for Claude.ai)

### 4. Set Up GitHub OAuth

1. Go to https://github.com/settings/developers
2. Create new OAuth App:
   - Application name: `Claude Credential Proxy`
   - Homepage URL: `https://ganymede.tail0410a7.ts.net:10000`
   - Authorization callback URL: `https://ganymede.tail0410a7.ts.net:10000/oauth/callback`
3. Generate client secret and add to `.env`:
   ```
   GITHUB_CLIENT_ID=<your-client-id>
   GITHUB_CLIENT_SECRET=<your-client-secret>
   GITHUB_ALLOWED_USERS=Jython1415  # Your GitHub username(s)
   BASE_URL=https://ganymede.tail0410a7.ts.net:10000
   ```

### 5. Add MCP Custom Connector in Claude.ai

The setup script will print your configuration. In Claude.ai:

1. Go to Settings > Connectors > Add Custom Connector
2. Enter Name: `Credential Proxy`
3. Enter URL: `https://ganymede.tail0410a7.ts.net:10000/mcp`
4. Click "Advanced settings":
   - OAuth Client ID: (from GitHub OAuth App)
   - OAuth Client Secret: (from GitHub OAuth App)
5. Click "Add" - you'll be redirected to GitHub to authorize

**Note:** Port 10000 is used because Tailscale Funnel only allows ports 443, 8443, and 10000.

## Usage in Claude.ai

Once connected, you can use the MCP tools:

```
# Create a session for API access
Use create_session with services: ["bsky", "git"]

# This returns session_id and proxy_url for use in scripts
```

Then in scripts:
```python
import os, requests

response = requests.get(
    f"{os.environ['PROXY_URL']}/proxy/bsky/app.bsky.feed.searchPosts",
    params={"q": "python", "limit": 10},
    headers={"X-Session-Id": os.environ['SESSION_ID']}
)
```

## Architecture

```
Claude.ai Browser
    │
    ├── MCP Custom Connector (port 8001)
    │       └── create_session / list_services / revoke_session
    │
    └── Skill Scripts (using SESSION_ID + PROXY_URL)
            │
            ├── /proxy/<service>/<path>  → Credential-injected API calls
            ├── /git/fetch-bundle        → Clone repo as bundle
            └── /git/push-bundle         → Push branch, create PR
            │
            └── Flask Server (port 8443)
                    │
                    └── Your APIs (Bluesky, GitHub, etc.)
```

## Server Management

```bash
# View logs
tail -f ~/Library/Logs/credential-proxy.log
tail -f ~/Library/Logs/mcp-server.log

# Restart servers
launchctl stop com.joshuashew.credential-proxy
launchctl start com.joshuashew.credential-proxy
launchctl stop com.joshuashew.mcp-server
launchctl start com.joshuashew.mcp-server

# Check status
launchctl list | grep joshuashew
```

## Documentation

- [CLAUDE.md](CLAUDE.md) - Technical reference for Claude Code
- [mcp/README.md](mcp/README.md) - MCP server setup
- [skills/bluesky-access/SKILL.md](skills/bluesky-access/SKILL.md) - Bluesky skill docs

## Available Skills

- **git-proxy** (`skills/git-proxy/`) - Git bundle proxy for cloning and pushing repositories
- **bluesky-access** (`skills/bluesky-access/`) - Bluesky/ATProtocol API access

Both skills use session-based authentication via the credential proxy. Legacy `X-Auth-Key` authentication is still supported for backward compatibility.

## License

MIT
