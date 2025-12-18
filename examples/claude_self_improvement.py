#!/usr/bin/env python3
"""
Example: Claude.ai managing its own project knowledge repository

This demonstrates the powerful use case where Claude can:
1. Clone its own project knowledge repository
2. Analyze the git history to understand context evolution
3. Identify improvements or gaps
4. Create feature branches with proposed changes
5. Push branches for team review
"""

from client.git_client import GitProxyClient
import os


class ClaudeProjectManager:
    """Manages Claude's own project knowledge via git"""

    def __init__(self, project_repo_url: str):
        self.client = GitProxyClient()
        self.project_repo_url = project_repo_url
        self.repo_path = None

    def setup(self):
        """Clone or update project repository"""
        print("Setting up project repository...")

        # Try to clone or pull latest
        try:
            self.repo_path = self.client.clone(self.project_repo_url)
            print(f"Cloned to: {self.repo_path}")
        except Exception as e:
            # Already exists, pull instead
            repo_name = self.project_repo_url.split('/')[-1].replace('.git', '')
            self.repo_path = os.path.join(self.client.workspace, repo_name)
            self.client.pull(self.repo_path)
            print(f"Updated: {self.repo_path}")

        return self.repo_path

    def analyze_history(self):
        """Analyze how project context evolved"""
        print("\nAnalyzing project history...")

        # Get recent commits
        history = self.client.log(self.repo_path, n=20)
        print(f"Recent commits:\n{history}")

        # Get current status
        status = self.client.status(self.repo_path, short=False)
        print(f"\nCurrent status:\n{status}")

        return {
            'history': history,
            'status': status
        }

    def propose_improvement(self, branch_name: str, description: str, changes: dict):
        """
        Create a feature branch with proposed improvements

        Args:
            branch_name: Name for the feature branch
            description: Description of the improvement
            changes: Dict mapping file paths to new content
        """
        print(f"\nProposing improvement: {description}")

        # Create feature branch
        self.client.branch(self.repo_path, f"claude/{branch_name}", checkout=True)

        # Make changes (in real usage, you would write to files)
        # For this example, we're just showing the structure
        print(f"Created branch: claude/{branch_name}")
        print(f"Changes to make: {list(changes.keys())}")

        # In real usage:
        # for file_path, content in changes.items():
        #     with open(os.path.join(self.repo_path, file_path), 'w') as f:
        #         f.write(content)

        # Commit
        commit_msg = f"Claude proposes: {description}"
        if self.client.commit(self.repo_path, commit_msg):
            print(f"Committed: {commit_msg}")

        # Push branch
        if self.client.push(self.repo_path, branch=f"claude/{branch_name}"):
            print(f"Pushed branch for review")

        return f"claude/{branch_name}"


def main():
    """Example workflow"""

    # Initialize manager for your project knowledge repo
    manager = ClaudeProjectManager(
        'https://github.com/yourusername/your-project-knowledge.git'
    )

    # Setup repository
    manager.setup()

    # Analyze current state
    analysis = manager.analyze_history()

    # Example: Propose adding error handling guidelines
    # (In real usage, Claude would analyze the repo and identify this need)
    improvement = {
        'branch_name': 'add-error-handling-guide',
        'description': 'Add comprehensive error handling guidelines',
        'changes': {
            'knowledge/error-handling.md': """
# Error Handling Guidelines

## Best Practices
1. Use specific exception types
2. Log errors with context
3. Provide user-friendly messages
4. Include recovery suggestions

## Examples
...
"""
        }
    }

    # Create branch with improvement
    branch = manager.propose_improvement(**improvement)

    print(f"\n✓ Improvement proposed in branch: {branch}")
    print("Team can now review and merge the PR")


if __name__ == '__main__':
    main()
