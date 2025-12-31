---
name: git-proxy
description: Clone GitHub repositories into Claude.ai Projects using git bundles via proxy server. Use when you need to work with git repositories from Claude.ai.
---

# Git Proxy Skill

Clone and push to GitHub repositories from Claude.ai Projects using git bundles and a proxy server.

## Setup (REQUIRED - Do This First!)

**1. Copy git_client.py to your project:**
```python
import subprocess
subprocess.run(['cp', '/mnt/skills/user/git-proxy/git_client.py', '/mnt/project/'], check=True)
```

**2. Load environment variables:**

Create `/mnt/project/_env` with:
```
GIT_PROXY_URL=https://your-machine.your-tailnet.ts.net
GIT_PROXY_KEY=your-secret-authentication-key
```

Then load it:
```python
import sys
sys.path.insert(0, '/mnt/project')
from git_client import load_env_from_file
load_env_from_file()
```

## Available Methods

**GitProxyClient has only 3 methods:**
- ✅ `health_check()` - Test connection
- ✅ `fetch_bundle(repo_url, output_path, branch='main')` - Download repo
- ✅ `push_bundle(bundle_path, repo_url, branch, ...)` - Upload and push

**Methods that DO NOT exist:**
- ❌ NO `clone()`, `push()`, or `pull()` methods

**Convenience functions:**
- `load_env_from_file()` - Load env vars from `/mnt/project/_env`
- `clone_repo(repo_url, target_dir)` - One-step: fetch + clone + config git user
- `setup_git_user(repo_dir)` - Configure git identity (auto-called by clone_repo)

## Quick Start

```python
import subprocess
from git_client import load_env_from_file, clone_repo, GitProxyClient

# Setup (do once per session)
subprocess.run(['cp', '/mnt/skills/user/git-proxy/git_client.py', '/mnt/project/'])
load_env_from_file()

# Clone repository
clone_repo('https://github.com/user/repo.git', '/tmp/repo')

# Make changes
with open('/tmp/repo/README.md', 'a') as f:
    f.write('\nChanges from Claude\n')

# Commit and create branch
subprocess.run(['git', 'add', '.'], cwd='/tmp/repo', check=True)
subprocess.run(['git', 'commit', '-m', 'Update'], cwd='/tmp/repo', check=True)
subprocess.run(['git', 'checkout', '-b', 'feature/update'], cwd='/tmp/repo', check=True)

# Create bundle with EXPLICIT branch name (NOT HEAD!)
subprocess.run([
    'git', 'bundle', 'create', '/tmp/changes.bundle',
    'origin/main..feature/update'  # Use branch name!
], cwd='/tmp/repo', check=True)

# Push and create PR
client = GitProxyClient()
result = client.push_bundle(
    '/tmp/changes.bundle',
    'https://github.com/user/repo.git',
    'feature/update',
    create_pr=True,
    pr_title='Updates from Claude'
)
print(f"PR: {result['pr_url']}")
```

## Critical: Bundle Creation

**ALWAYS use explicit branch refs when pushing:**

❌ **Wrong:** `git bundle create file.bundle origin/main..HEAD`
✅ **Correct:** `git bundle create file.bundle origin/main..branch-name`

Using `HEAD` causes "Couldn't find remote ref" errors. Use the actual branch name.

## Common Issues

**Import fails?**
```python
# Copy git_client.py first:
subprocess.run(['cp', '/mnt/skills/user/git-proxy/git_client.py', '/mnt/project/'])
```

**ValueError: Missing proxy_url or auth_key?**
```python
# Load env vars:
load_env_from_file()
```

**401 Unauthorized?**
- Verify `GIT_PROXY_KEY` in `/mnt/project/_env` matches server's `PROXY_SECRET_KEY`

**404 Not Found?**
- Only 3 endpoints: `/health`, `/git/fetch-bundle`, `/git/push-bundle`
- Don't try `/clone`, `/git-exec`, etc.

**Bundle push fails with "Couldn't find remote ref"?**
- Use explicit branch name in bundle: `origin/main..feature-branch` (not `HEAD`)

**"Author identity unknown"?**
- Use `clone_repo()` (auto-configures) OR manually:
  ```python
  subprocess.run(['git', 'config', 'user.email', 'claude@anthropic.com'], cwd='/tmp/repo')
  subprocess.run(['git', 'config', 'user.name', 'Claude'], cwd='/tmp/repo')
  ```

**PR not created automatically?**
- Check server logs - gh CLI must be detected at startup
- If unavailable, use `manual_pr_url` from response

## Manual Workflow (Without Convenience Functions)

```python
from git_client import GitProxyClient
import subprocess

client = GitProxyClient()

# Fetch bundle
client.fetch_bundle('https://github.com/user/repo.git', '/tmp/repo.bundle')

# Clone
subprocess.run(['git', 'clone', '/tmp/repo.bundle', '/tmp/repo'], check=True)
subprocess.run(['git', 'remote', 'set-url', 'origin', 'https://github.com/user/repo.git'], cwd='/tmp/repo', check=True)
subprocess.run(['git', 'config', 'user.email', 'claude@anthropic.com'], cwd='/tmp/repo', check=True)
subprocess.run(['git', 'config', 'user.name', 'Claude'], cwd='/tmp/repo', check=True)

# [Make changes, commit, create branch, create bundle]

# Push
result = client.push_bundle('/tmp/changes.bundle', 'https://github.com/user/repo.git', 'branch-name', create_pr=True)
```

## Security

- All operations require authentication via secret key
- Files processed in temporary directories with automatic cleanup
- No persistent storage on proxy server
- PR creation uses your local gh CLI and git credentials
