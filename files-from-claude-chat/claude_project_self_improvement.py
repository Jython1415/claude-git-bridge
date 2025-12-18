"""
Example: Claude.ai Project Managing Its Own GitHub Context

This demonstrates the powerful use case you described:
Claude can examine the git history of its own Project knowledge,
propose improvements, and create PRs for team review.
"""

from git_proxy_client import *
import os
import json

# Configuration for the project
PROJECT_REPO = "https://github.com/joshuashew/claude-project-knowledge.git"
PROJECT_PATH = f"{Config.WORKSPACE}/claude-project-knowledge"

def setup_project_repo():
    """Initial setup: clone the project knowledge repo"""
    if not os.path.exists(PROJECT_PATH):
        print("Cloning project knowledge repository...")
        git_clone(PROJECT_REPO, PROJECT_PATH)
    else:
        # Pull latest
        git_exec("git pull", cwd=PROJECT_PATH)
    
    return PROJECT_PATH

def analyze_project_history():
    """Analyze how this project's context evolved"""
    
    # Get commit history
    history = git_log(PROJECT_PATH, n=50)
    
    # Get file change stats
    stats_cmd = "git log --pretty=format: --name-only --since='1 month ago' | sort | uniq -c | sort -rn"
    stdout, _, _ = git_exec(stats_cmd, cwd=PROJECT_PATH)
    
    return {
        'recent_commits': history,
        'most_changed_files': stdout,
        'total_files': len(os.listdir(f"{PROJECT_PATH}/knowledge"))
    }

def propose_context_improvement(analysis, suggestion):
    """
    Claude proposes an improvement to its own project context
    Creates a branch and returns changes for review
    """
    
    # Create feature branch
    branch_name = f"claude/improve-{suggestion['filename']}"
    git_exec(f"git checkout -b {branch_name}", cwd=PROJECT_PATH)
    
    # Make the changes
    file_path = f"{PROJECT_PATH}/knowledge/{suggestion['filename']}"
    with open(file_path, 'w') as f:
        f.write(suggestion['new_content'])
    
    # Commit
    git_commit(
        PROJECT_PATH,
        f"Claude suggests: {suggestion['description']}",
        files=[f"knowledge/{suggestion['filename']}"]
    )
    
    # Push branch
    git_push(PROJECT_PATH, branch=branch_name)
    
    return branch_name

def create_pr_for_review(branch_name, description):
    """
    After pushing branch, create PR using GitHub API
    (This would use api.github.com if whitelisted)
    """
    
    # This is where you'd call GitHub API to create PR
    # See: POST /repos/{owner}/{repo}/pulls
    
    pr_data = {
        'title': f'[Claude] {description}',
        'head': branch_name,
        'base': 'main',
        'body': f"""
        This PR was created by Claude after analyzing the project context.
        
        **Analysis:**
        {description}
        
        **Changes:**
        - See commit history for details
        
        Please review and merge if appropriate.
        """
    }
    
    # Would POST to api.github.com here
    # For now, return the data structure
    return pr_data

# Example workflow
def claude_self_improves():
    """
    Complete workflow: Claude examines its own context,
    identifies improvements, and proposes changes
    """
    
    # 1. Setup
    setup_project_repo()
    
    # 2. Analyze history
    analysis = analyze_project_history()
    print(f"Analyzed {analysis['total_files']} knowledge files")
    print(f"Recent commits:\n{analysis['recent_commits']}")
    
    # 3. Claude identifies improvement opportunity
    # (In practice, Claude would analyze files and determine what to improve)
    suggestion = {
        'filename': 'development-guidelines.md',
        'description': 'Add section on error handling patterns',
        'new_content': """
        # Development Guidelines
        
        ## Error Handling
        - Always use try/except with specific exception types
        - Log errors with context
        - Return user-friendly messages
        
        ... (rest of content)
        """
    }
    
    # 4. Create branch and commit
    branch = propose_context_improvement(analysis, suggestion)
    
    # 5. Create PR for human review
    pr = create_pr_for_review(branch, suggestion['description'])
    
    print(f"Created branch: {branch}")
    print(f"PR ready for review: {pr}")
    
    return {
        'branch': branch,
        'pr_url': f"https://github.com/joshuashew/claude-project-knowledge/pulls"
    }

if __name__ == '__main__':
    result = claude_self_improves()
    print(json.dumps(result, indent=2))
