# Credential Proxy MCP Server

MCP server providing session management for the credential proxy. Works as a Claude.ai custom connector.

## Prerequisites

- Python 3.10+
- Flask server running (port 8443)
- Tailscale for network access

## Installation

```bash
cd /path/to/claude-git-bridge
uv pip install -r requirements.txt
```

## Running Locally

1. Start the Flask server (in one terminal):
   ```bash
   (cd server && uv run proxy_server.py)
   ```

2. Start the MCP server (in another terminal):
   ```bash
   (cd mcp && FLASK_URL=http://localhost:8443 uv run server.py)
   ```

## Claude.ai Custom Connector Setup

1. Expose both servers via Tailscale Funnel:
   ```bash
   # Flask server
   tailscale serve --bg --https=8443 http://127.0.0.1:8443
   tailscale funnel 8443

   # MCP server
   tailscale serve --bg --https=8001 http://127.0.0.1:8001
   tailscale funnel 8001
   ```

2. In Claude.ai, go to Settings > Connectors > Add Custom Connector

3. Enter the MCP server URL:
   ```
   https://<your-machine>.<tailnet>.ts.net:8001/mcp
   ```

4. Leave authentication empty (Tailscale provides network security)

5. Click "Add" to connect

## Available Tools

### create_session

Create a session granting access to specified services.

```
create_session(services=["bsky", "git"], ttl_minutes=30)
```

Returns:
- `session_id`: Use in `X-Session-Id` header
- `proxy_url`: Base URL for proxy requests
- `expires_in_minutes`: Session lifetime

### revoke_session

Revoke an active session immediately.

```
revoke_session(session_id="...")
```

### list_services

List all available services.

```
list_services()
```

## Usage in Skills

After creating a session, use the returned values in your scripts:

```python
import os
import requests

SESSION_ID = os.environ['SESSION_ID']  # From create_session
PROXY_URL = os.environ['PROXY_URL']    # From create_session

# Example: Query Bluesky
response = requests.get(
    f"{PROXY_URL}/proxy/bsky/app.bsky.feed.searchPosts",
    params={"q": "python", "limit": 10},
    headers={"X-Session-Id": SESSION_ID}
)
print(response.json())
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_URL` | `http://localhost:8443` | Flask server URL |
| `MCP_PORT` | `8001` | MCP server port |

## Troubleshooting

### MCP server can't connect to Flask
- Ensure Flask server is running
- Check `FLASK_URL` environment variable
- Verify no firewall blocking localhost connections

### Claude.ai can't connect to MCP
- Verify Tailscale Funnel is running: `tailscale funnel status`
- Check the URL is correct (port 8001, /mcp path)
- Ensure your Tailscale account has Funnel enabled

### Session creation fails
- Check Flask server logs for errors
- Verify credentials.json exists with valid service configs
