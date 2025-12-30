#!/usr/bin/env python3
"""
MCP Server for Credential Proxy Session Management

Exposes session management as MCP tools for Claude.ai custom connector.
Uses Streamable HTTP transport for compatibility with Claude.ai browser.
"""

import os
import httpx
from mcp.server.fastmcp import FastMCP

# Configuration
FLASK_URL = os.environ.get('FLASK_URL', 'http://localhost:8443')

# Initialize MCP server
mcp = FastMCP(
    "credential-proxy",
    stateless_http=True  # Important for scalability with remote connections
)


@mcp.tool()
async def create_session(services: list[str], ttl_minutes: int = 30) -> dict:
    """
    Create a new session granting access to specified services.

    Use this to get a session_id and proxy_url for accessing APIs through
    the credential proxy. The session will automatically expire after the
    specified TTL.

    Args:
        services: List of service names to grant access to.
                  Common services: "bsky" (Bluesky), "github_api", "git"
                  Use list_services() to see all available services.
        ttl_minutes: Session lifetime in minutes (default: 30, max: 480)

    Returns:
        Dictionary containing:
        - session_id: Use this in X-Session-Id header for requests
        - proxy_url: Base URL for proxy requests
        - expires_in_minutes: Session lifetime
        - services: List of services this session can access

    Example:
        result = create_session(["bsky", "git"], ttl_minutes=60)
        # Use result["session_id"] and result["proxy_url"] in your scripts
    """
    # Validate TTL
    if ttl_minutes < 1:
        return {"error": "ttl_minutes must be at least 1"}
    if ttl_minutes > 480:  # 8 hours max
        return {"error": "ttl_minutes cannot exceed 480 (8 hours)"}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{FLASK_URL}/sessions",
                json={"services": services, "ttl_minutes": ttl_minutes},
                timeout=10
            )

            if response.status_code == 400:
                return response.json()

            response.raise_for_status()
            return response.json()

    except httpx.TimeoutException:
        return {"error": "timeout connecting to proxy server"}
    except httpx.ConnectError:
        return {"error": f"could not connect to proxy server at {FLASK_URL}"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def revoke_session(session_id: str) -> dict:
    """
    Revoke an active session immediately.

    Use this to invalidate a session before its natural expiry.
    After revocation, the session_id can no longer be used.

    Args:
        session_id: The session ID to revoke

    Returns:
        Dictionary with status ("revoked") or error message
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{FLASK_URL}/sessions/{session_id}",
                timeout=10
            )

            if response.status_code == 404:
                return {"status": "not_found", "message": "Session not found or already expired"}

            response.raise_for_status()
            return response.json()

    except httpx.TimeoutException:
        return {"error": "timeout connecting to proxy server"}
    except httpx.ConnectError:
        return {"error": f"could not connect to proxy server at {FLASK_URL}"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def list_services() -> dict:
    """
    List all available services that can be included in sessions.

    Returns the names of services configured on the proxy server.
    Use these names when calling create_session().

    Returns:
        Dictionary with "services" key containing list of service names.
        Always includes "git" for git bundle operations.

    Common services:
        - "git": Git bundle operations (clone, push via bundles)
        - "bsky": Bluesky/ATProtocol API
        - "github_api": GitHub REST API
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{FLASK_URL}/services",
                timeout=10
            )
            response.raise_for_status()
            return response.json()

    except httpx.TimeoutException:
        return {"error": "timeout connecting to proxy server"}
    except httpx.ConnectError:
        return {"error": f"could not connect to proxy server at {FLASK_URL}"}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    port = int(os.environ.get('MCP_PORT', 8001))
    logger.info(f"Starting MCP server on port {port}")
    logger.info(f"Flask backend: {FLASK_URL}")

    # Run with Streamable HTTP transport for Claude.ai custom connector
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=port
    )
