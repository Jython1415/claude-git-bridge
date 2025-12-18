"""
Git Proxy Client for Claude.ai Skills
Allows full git operations via HTTPS tunnel to local/remote proxy
"""

import requests
import base64
import os
import json

# Configuration - loaded from environment or config file
class Config:
    PROXY_URL = os.environ.get('GIT_PROXY_URL', 'https://your-ngrok-url.ngrok-free.app')
    AUTH_KEY = os.environ.get('GIT_PROXY_KEY', 'your-secret-key')
    WORKSPACE = '/home/claude/git-workspace'

def git_exec(command, cwd=None):
    """Execute git command via proxy"""
    
    if cwd is None:
        cwd = Config.WORKSPACE
    
    # Encode command
    encoded_cmd = base64.b64encode(command.encode()).decode()
    
    # Send to proxy
    response = requests.post(
        f'{Config.PROXY_URL}/git-exec',
        json={
            'command': encoded_cmd,
            'cwd': cwd
        },
        headers={'X-Auth-Key': Config.AUTH_KEY},
        timeout=120
    )
    
    if response.status_code != 200:
        raise Exception(f"Proxy error: {response.status_code} - {response.text}")
    
    result = response.json()
    
    # Decode results
    stdout = base64.b64decode(result['stdout']).decode('utf-8', errors='replace')
    stderr = base64.b64decode(result['stderr']).decode('utf-8', errors='replace')
    
    return stdout, stderr, result['returncode']

# High-level git operations
def git_clone(repo_url, local_path=None):
    """Clone a repository"""
    if local_path is None:
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        local_path = f"{Config.WORKSPACE}/{repo_name}"
    
    cmd = f"git clone {repo_url} {local_path}"
    stdout, stderr, code = git_exec(cmd, cwd=Config.WORKSPACE)
    
    if code != 0:
        raise Exception(f"Clone failed: {stderr}")
    
    return local_path

def git_status(repo_path):
    """Get git status"""
    stdout, stderr, code = git_exec("git status --short", cwd=repo_path)
    return stdout

def git_commit(repo_path, message, files=None):
    """Commit changes"""
    if files:
        for file in files:
            git_exec(f"git add {file}", cwd=repo_path)
    else:
        git_exec("git add -A", cwd=repo_path)
    
    stdout, stderr, code = git_exec(
        f'git commit -m "{message}"', 
        cwd=repo_path
    )
    return code == 0

def git_push(repo_path, branch='main'):
    """Push changes"""
    stdout, stderr, code = git_exec(
        f"git push origin {branch}", 
        cwd=repo_path
    )
    return code == 0

def git_log(repo_path, n=10):
    """Get commit history"""
    stdout, stderr, code = git_exec(
        f"git log --oneline -n {n}", 
        cwd=repo_path
    )
    return stdout

# Example usage
if __name__ == '__main__':
    # Clone a repo
    repo_path = git_clone('https://github.com/user/repo.git')
    print(f"Cloned to: {repo_path}")
    
    # Check status
    status = git_status(repo_path)
    print(f"Status:\n{status}")
    
    # Make changes (example)
    # ... modify files ...
    
    # Commit and push
    git_commit(repo_path, "Update from Claude.ai skill")
    git_push(repo_path)
