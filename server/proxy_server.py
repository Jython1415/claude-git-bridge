#!/usr/bin/env python3
"""
Git Proxy Server
Executes git commands on behalf of Claude.ai skills via HTTPS
"""

from flask import Flask, request, jsonify
import subprocess
import base64
import os
import logging
from datetime import datetime
from pathlib import Path

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, will use system env vars

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
SECRET_KEY = os.environ.get('PROXY_SECRET_KEY')
if not SECRET_KEY:
    logger.warning("PROXY_SECRET_KEY not set! Using insecure default.")
    SECRET_KEY = 'CHANGE-ME-INSECURE'

WORKSPACE_DIR = Path(os.environ.get('GIT_WORKSPACE', os.path.expanduser('~/git-proxy-workspace')))
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

# Request logging
REQUEST_LOG = WORKSPACE_DIR / 'requests.log'


def log_request(endpoint, status, details=''):
    """Log all requests for audit trail"""
    with open(REQUEST_LOG, 'a') as f:
        timestamp = datetime.now().isoformat()
        f.write(f"{timestamp} | {endpoint} | {status} | {details}\n")


def verify_auth(auth_header):
    """Verify authentication token"""
    return auth_header == SECRET_KEY


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'workspace': str(WORKSPACE_DIR),
        'timestamp': datetime.now().isoformat()
    })


@app.route('/git-exec', methods=['POST'])
def git_exec():
    """Execute git command"""

    # Verify authentication
    auth_key = request.headers.get('X-Auth-Key')
    if not verify_auth(auth_key):
        log_request('/git-exec', 'UNAUTHORIZED', 'Invalid auth key')
        return jsonify({'error': 'unauthorized'}), 401

    try:
        data = request.json

        # Decode command
        encoded_cmd = data.get('command')
        if not encoded_cmd:
            return jsonify({'error': 'missing command'}), 400

        git_cmd = base64.b64decode(encoded_cmd).decode('utf-8')

        # Security: only allow git commands
        if not git_cmd.strip().startswith('git '):
            log_request('/git-exec', 'FORBIDDEN', f'Non-git command: {git_cmd}')
            return jsonify({'error': 'only git commands allowed'}), 403

        # Get working directory
        cwd = data.get('cwd', str(WORKSPACE_DIR))
        cwd_path = Path(cwd)

        # Security: ensure cwd is within workspace
        try:
            cwd_path.resolve().relative_to(WORKSPACE_DIR.resolve())
        except ValueError:
            # If cwd is not relative to workspace, use workspace
            cwd_path = WORKSPACE_DIR

        # Ensure directory exists
        cwd_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Executing: {git_cmd} in {cwd_path}")
        log_request('/git-exec', 'EXECUTING', git_cmd)

        # Execute command
        result = subprocess.run(
            git_cmd,
            shell=True,
            capture_output=True,
            timeout=60,
            cwd=str(cwd_path)
        )

        # Encode results
        response = {
            'stdout': base64.b64encode(result.stdout).decode('utf-8'),
            'stderr': base64.b64encode(result.stderr).decode('utf-8'),
            'returncode': result.returncode
        }

        log_request('/git-exec', 'SUCCESS', f'returncode={result.returncode}')
        return jsonify(response)

    except subprocess.TimeoutExpired:
        log_request('/git-exec', 'TIMEOUT', git_cmd)
        return jsonify({'error': 'command timeout'}), 408

    except Exception as e:
        logger.error(f"Error executing command: {e}")
        log_request('/git-exec', 'ERROR', str(e))
        return jsonify({'error': str(e)}), 500


@app.route('/workspace/list', methods=['GET'])
def list_workspace():
    """List repositories in workspace"""

    # Verify authentication
    auth_key = request.headers.get('X-Auth-Key')
    if not verify_auth(auth_key):
        return jsonify({'error': 'unauthorized'}), 401

    try:
        repos = []
        for item in WORKSPACE_DIR.iterdir():
            if item.is_dir() and (item / '.git').exists():
                repos.append({
                    'name': item.name,
                    'path': str(item)
                })

        return jsonify({'repositories': repos})

    except Exception as e:
        logger.error(f"Error listing workspace: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    logger.info(f"Starting Git Proxy Server")
    logger.info(f"Workspace: {WORKSPACE_DIR}")
    logger.info(f"Secret key configured: {bool(os.environ.get('PROXY_SECRET_KEY'))}")

    # Run server
    app.run(
        host='127.0.0.1',
        port=int(os.environ.get('PORT', 8443)),
        debug=os.environ.get('DEBUG', 'False').lower() == 'true'
    )
