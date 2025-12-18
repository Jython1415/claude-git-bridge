# API Credential Patterns for Claude.ai Skills

Based on analysis of existing skills (like oaustegard/claude-skills), here are proven patterns:

## Pattern 1: Environment Variables (Most Common)

### In your skill's Python script:
```python
import os

# Load from environment
PROXY_URL = os.environ.get('GIT_PROXY_URL')
AUTH_KEY = os.environ.get('GIT_PROXY_KEY')

# Validate they exist
if not PROXY_URL or not AUTH_KEY:
    raise ValueError("Missing required environment variables: GIT_PROXY_URL, GIT_PROXY_KEY")
```

### Setting environment variables in skills:

**Option A: .env file in skill directory**
```bash
# /mnt/skills/user/git-proxy/.env
GIT_PROXY_URL=https://claude-proxy.joshuashew.com
GIT_PROXY_KEY=your-secret-key-here
```

```python
# In your script
from dotenv import load_dotenv
load_dotenv('/mnt/skills/user/git-proxy/.env')
```

**Option B: System environment (if Claude.ai supports this)**
Some skills can reference system-level environment variables if configured.

---

## Pattern 2: Config File (Flexible)

### JSON configuration:
```python
# /mnt/skills/user/git-proxy/config.json
{
    "proxy": {
        "url": "https://claude-proxy.joshuashew.com",
        "auth_key": "your-secret-key-here",
        "timeout": 120,
        "workspace": "~/git-proxy-workspace"
    },
    "github": {
        "default_branch": "main",
        "commit_author": "Claude AI <claude@anthropic.com>"
    }
}
```

```python
# In your skill
import json
import os

config_path = '/mnt/skills/user/git-proxy/config.json'
with open(config_path) as f:
    config = json.load(f)

PROXY_URL = config['proxy']['url']
AUTH_KEY = config['proxy']['auth_key']
```

---

## Pattern 3: Encrypted Secrets (Most Secure)

### Setup (one-time):
```python
from cryptography.fernet import Fernet
import base64

# Generate encryption key (store this somewhere safe!)
key = Fernet.generate_key()
print(f"Encryption key (save this): {key.decode()}")

# Encrypt your secrets
cipher = Fernet(key)
encrypted_auth = cipher.encrypt(b"your-secret-key-here")
encrypted_url = cipher.encrypt(b"https://claude-proxy.joshuashew.com")

# Save encrypted values
print(f"Encrypted auth: {encrypted_auth.decode()}")
print(f"Encrypted URL: {encrypted_url.decode()}")
```

### In skill:
```python
from cryptography.fernet import Fernet
import os

# Encryption key from environment (only this needs to be secret)
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
cipher = Fernet(ENCRYPTION_KEY.encode())

# Encrypted secrets (safe to commit to git)
ENCRYPTED_URL = b"gAAAAABh..."
ENCRYPTED_AUTH = b"gAAAAABh..."

# Decrypt at runtime
PROXY_URL = cipher.decrypt(ENCRYPTED_URL).decode()
AUTH_KEY = cipher.decrypt(ENCRYPTED_AUTH).decode()
```

---

## Pattern 4: Per-User Credentials (Team Skills)

For skills shared with a team where each person has their own credentials:

```python
# /mnt/skills/user/git-proxy/credentials/
# ├── joshua.json
# ├── teammate1.json
# └── teammate2.json

import os
import json

# Determine current user
USER = os.environ.get('CLAUDE_USER', 'joshua')
cred_file = f'/mnt/skills/user/git-proxy/credentials/{USER}.json'

with open(cred_file) as f:
    creds = json.load(f)

PROXY_URL = creds['proxy_url']
AUTH_KEY = creds['auth_key']
```

---

## Pattern 5: Dynamic Token Refresh (OAuth)

For services requiring token refresh:

```python
import json
import time
import requests
from datetime import datetime, timedelta

class TokenManager:
    def __init__(self, config_file):
        self.config_file = config_file
        self.load_token()
    
    def load_token(self):
        with open(self.config_file) as f:
            data = json.load(f)
        
        self.access_token = data['access_token']
        self.refresh_token = data['refresh_token']
        self.expires_at = datetime.fromisoformat(data['expires_at'])
    
    def save_token(self):
        with open(self.config_file, 'w') as f:
            json.dump({
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
                'expires_at': self.expires_at.isoformat()
            }, f)
    
    def get_token(self):
        """Get valid token, refreshing if needed"""
        if datetime.now() >= self.expires_at:
            self.refresh()
        return self.access_token
    
    def refresh(self):
        """Refresh the access token"""
        response = requests.post(
            'https://auth.example.com/token',
            data={
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token
            }
        )
        data = response.json()
        
        self.access_token = data['access_token']
        self.refresh_token = data.get('refresh_token', self.refresh_token)
        self.expires_at = datetime.now() + timedelta(seconds=data['expires_in'])
        
        self.save_token()

# Usage
token_mgr = TokenManager('/mnt/skills/user/git-proxy/tokens.json')
AUTH_KEY = token_mgr.get_token()
```

---

## Pattern 6: Credential Helper (Secure Input)

For interactive credential entry (first-time setup):

```python
import os
import json
import getpass

CRED_FILE = '/mnt/skills/user/git-proxy/credentials.json'

def setup_credentials():
    """Interactive setup for first-time use"""
    print("Git Proxy Setup")
    print("-" * 50)
    
    proxy_url = input("Proxy URL (e.g., https://claude-proxy.joshuashew.com): ")
    auth_key = getpass.getpass("Authentication key: ")
    
    # Save
    with open(CRED_FILE, 'w') as f:
        json.dump({
            'proxy_url': proxy_url,
            'auth_key': auth_key,
            'created_at': datetime.now().isoformat()
        }, f)
    
    print(f"✓ Credentials saved to {CRED_FILE}")

def load_credentials():
    """Load existing credentials or prompt for setup"""
    if not os.path.exists(CRED_FILE):
        print("No credentials found. Running setup...")
        setup_credentials()
    
    with open(CRED_FILE) as f:
        return json.load(f)

# Usage
creds = load_credentials()
PROXY_URL = creds['proxy_url']
AUTH_KEY = creds['auth_key']
```

---

## Recommended Approach for Git Proxy

### For personal use:
```python
# Simple config file
# /mnt/skills/user/git-proxy/config.json
{
    "proxy_url": "https://claude-proxy.joshuashew.com",
    "auth_key": "generate-random-key-with-openssl-rand",
    "timeout": 120
}
```

### For team/shared use:
```python
# Each team member has their own config
# /mnt/skills/user/git-proxy/config.joshua.json
{
    "proxy_url": "https://joshua-proxy.joshuashew.com",
    "auth_key": "joshua-specific-key"
}

# Determine user from environment or prompt
USER = os.environ.get('USER', 'joshua')
config_file = f'/mnt/skills/user/git-proxy/config.{USER}.json'
```

---

## Security Best Practices

### ✅ DO:
- Use .env files for local development
- Encrypt sensitive values if config is committed to git
- Use environment variables for production
- Rotate credentials periodically
- Use separate credentials per team member
- Set appropriate file permissions (chmod 600)

### ❌ DON'T:
- Hardcode credentials in source code
- Commit unencrypted credentials to git
- Share credentials across team members
- Use same credentials for dev/prod
- Store credentials in skill descriptions

---

## Example: Complete Credential Setup

```python
#!/usr/bin/env python3
"""
Complete credential management for git-proxy skill
Supports: config file, environment variables, encryption
"""

import os
import json
from pathlib import Path
from cryptography.fernet import Fernet

class CredentialManager:
    def __init__(self, skill_dir='/mnt/skills/user/git-proxy'):
        self.skill_dir = Path(skill_dir)
        self.config_file = self.skill_dir / 'config.json'
        self.env_file = self.skill_dir / '.env'
    
    def load(self):
        """Load credentials from best available source"""
        
        # Priority 1: Environment variables
        if os.environ.get('GIT_PROXY_URL'):
            return {
                'proxy_url': os.environ['GIT_PROXY_URL'],
                'auth_key': os.environ['GIT_PROXY_KEY']
            }
        
        # Priority 2: Config file
        if self.config_file.exists():
            with open(self.config_file) as f:
                config = json.load(f)
            
            # If encrypted
            if 'encrypted' in config:
                key = os.environ.get('ENCRYPTION_KEY')
                if not key:
                    raise ValueError("Config is encrypted but ENCRYPTION_KEY not set")
                
                cipher = Fernet(key.encode())
                return {
                    'proxy_url': cipher.decrypt(config['proxy_url'].encode()).decode(),
                    'auth_key': cipher.decrypt(config['auth_key'].encode()).decode()
                }
            
            # Plain config
            return config
        
        # Priority 3: Interactive setup
        return self.setup_interactive()
    
    def setup_interactive(self):
        """Prompt user for credentials"""
        print("Git Proxy credential setup")
        proxy_url = input("Proxy URL: ")
        auth_key = input("Auth key: ")
        
        # Save to config
        config = {
            'proxy_url': proxy_url,
            'auth_key': auth_key
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✓ Saved to {self.config_file}")
        return config

# Usage in your skill:
cred_mgr = CredentialManager()
creds = cred_mgr.load()

PROXY_URL = creds['proxy_url']
AUTH_KEY = creds['auth_key']
```

---

## Testing Credentials

```python
def test_credentials():
    """Verify proxy credentials work"""
    try:
        response = requests.get(
            f'{PROXY_URL}/health',
            headers={'X-Auth-Key': AUTH_KEY},
            timeout=5
        )
        
        if response.status_code == 200:
            print("✓ Credentials valid")
            return True
        else:
            print(f"✗ Auth failed: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

# Run on skill load
if __name__ == '__main__':
    if test_credentials():
        print("Ready to use git proxy")
    else:
        print("Please check credentials")
```
