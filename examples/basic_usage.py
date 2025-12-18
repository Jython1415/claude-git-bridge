#!/usr/bin/env python3
"""
Basic usage example for git proxy client
"""

from client.git_client import GitProxyClient

def main():
    # Initialize client
    # Reads GIT_PROXY_URL and GIT_PROXY_KEY from environment
    client = GitProxyClient()

    # Check server health
    print("Checking proxy health...")
    health = client.health_check()
    print(f"Server status: {health['status']}")
    print(f"Workspace: {health['workspace']}")

    # Clone a repository
    print("\nCloning repository...")
    repo_path = client.clone('https://github.com/user/example-repo.git')
    print(f"Cloned to: {repo_path}")

    # Check status
    print("\nChecking status...")
    status = client.status(repo_path)
    print(status)

    # Make some changes (example - you would modify files here)
    # ...

    # Commit changes
    print("\nCommitting changes...")
    if client.commit(repo_path, "Update from Claude git bridge"):
        print("Commit successful")

    # Push to remote
    print("\nPushing changes...")
    if client.push(repo_path):
        print("Push successful")

    # View log
    print("\nRecent commits:")
    log = client.log(repo_path, n=5)
    print(log)


if __name__ == '__main__':
    main()
