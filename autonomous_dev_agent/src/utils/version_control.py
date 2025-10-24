"""
Version control integration for GitHub and GitLab.
"""
from typing import Dict, Any, List, Optional
import os
import base64
import requests
import json

from autonomous_dev_agent.src.config.config import settings


class GitHubClient:
    """
    Client for interacting with GitHub API.
    """
    
    def __init__(self, token: str = None, username: str = None, repo: str = None):
        """
        Initialize the GitHub client.
        
        Args:
            token: GitHub personal access token
            username: GitHub username
            repo: GitHub repository name
        """
        self.token = token or settings.GITHUB_TOKEN
        self.username = username or settings.GITHUB_USERNAME
        self.repo = repo or settings.GITHUB_REPO
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def get_repo_info(self) -> Dict[str, Any]:
        """
        Get information about the repository.
        
        Returns:
            Repository information
        """
        url = f"{self.base_url}/repos/{self.username}/{self.repo}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_branches(self) -> List[Dict[str, Any]]:
        """
        Get list of branches in the repository.
        
        Returns:
            List of branches
        """
        url = f"{self.base_url}/repos/{self.username}/{self.repo}/branches"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def create_branch(self, branch_name: str, base_branch: str = "main") -> Dict[str, Any]:
        """
        Create a new branch in the repository.
        
        Args:
            branch_name: Name of the new branch
            base_branch: Name of the base branch
            
        Returns:
            Result of branch creation
        """
        # Get the SHA of the base branch
        url = f"{self.base_url}/repos/{self.username}/{self.repo}/git/refs/heads/{base_branch}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        base_sha = response.json()["object"]["sha"]
        
        # Create the new branch
        url = f"{self.base_url}/repos/{self.username}/{self.repo}/git/refs"
        data = {
            "ref": f"refs/heads/{branch_name}",
            "sha": base_sha
        }
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()
    
    def get_file_content(self, file_path: str, branch: str = "main") -> Dict[str, Any]:
        """
        Get content of a file in the repository.
        
        Args:
            file_path: Path to the file
            branch: Branch name
            
        Returns:
            File content information
        """
        url = f"{self.base_url}/repos/{self.username}/{self.repo}/contents/{file_path}?ref={branch}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def create_or_update_file(self, file_path: str, content: str, commit_message: str, branch: str = "main") -> Dict[str, Any]:
        """
        Create or update a file in the repository.
        
        Args:
            file_path: Path to the file
            content: Content of the file
            commit_message: Commit message
            branch: Branch name
            
        Returns:
            Result of file creation/update
        """
        url = f"{self.base_url}/repos/{self.username}/{self.repo}/contents/{file_path}"
        
        # Check if file exists
        try:
            file_info = self.get_file_content(file_path, branch)
            sha = file_info["sha"]
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                # File doesn't exist
                sha = None
            else:
                raise
        
        # Encode content
        encoded_content = base64.b64encode(content.encode()).decode()
        
        # Prepare data
        data = {
            "message": commit_message,
            "content": encoded_content,
            "branch": branch
        }
        
        if sha:
            data["sha"] = sha
        
        # Create or update file
        response = requests.put(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()
    
    def create_pull_request(self, title: str, body: str, head_branch: str, base_branch: str = "main") -> Dict[str, Any]:
        """
        Create a pull request.
        
        Args:
            title: Title of the pull request
            body: Body of the pull request
            head_branch: Head branch name
            base_branch: Base branch name
            
        Returns:
            Pull request information
        """
        url = f"{self.base_url}/repos/{self.username}/{self.repo}/pulls"
        data = {
            "title": title,
            "body": body,
            "head": head_branch,
            "base": base_branch
        }
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()


class GitLabClient:
    """
    Client for interacting with GitLab API.
    """
    
    def __init__(self, token: str = None, project_id: str = None):
        """
        Initialize the GitLab client.
        
        Args:
            token: GitLab personal access token
            project_id: GitLab project ID
        """
        self.token = token or os.getenv("GITLAB_TOKEN", "")
        self.project_id = project_id or os.getenv("GITLAB_PROJECT_ID", "")
        self.base_url = "https://gitlab.com/api/v4"
        self.headers = {
            "PRIVATE-TOKEN": self.token
        }
    
    def get_project_info(self) -> Dict[str, Any]:
        """
        Get information about the project.
        
        Returns:
            Project information
        """
        url = f"{self.base_url}/projects/{self.project_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_branches(self) -> List[Dict[str, Any]]:
        """
        Get list of branches in the project.
        
        Returns:
            List of branches
        """
        url = f"{self.base_url}/projects/{self.project_id}/repository/branches"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def create_branch(self, branch_name: str, ref: str = "main") -> Dict[str, Any]:
        """
        Create a new branch in the project.
        
        Args:
            branch_name: Name of the new branch
            ref: Reference branch or commit
            
        Returns:
            Result of branch creation
        """
        url = f"{self.base_url}/projects/{self.project_id}/repository/branches"
        data = {
            "branch": branch_name,
            "ref": ref
        }
        response = requests.post(url, headers=self.headers, data=data)
        response.raise_for_status()
        return response.json()
    
    def get_file_content(self, file_path: str, ref: str = "main") -> Dict[str, Any]:
        """
        Get content of a file in the project.
        
        Args:
            file_path: Path to the file
            ref: Branch name or commit
            
        Returns:
            File content information
        """
        url = f"{self.base_url}/projects/{self.project_id}/repository/files/{file_path}/raw"
        params = {"ref": ref}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return {"content": response.text}
    
    def create_or_update_file(self, file_path: str, content: str, commit_message: str, branch: str = "main") -> Dict[str, Any]:
        """
        Create or update a file in the project.
        
        Args:
            file_path: Path to the file
            content: Content of the file
            commit_message: Commit message
            branch: Branch name
            
        Returns:
            Result of file creation/update
        """
        url = f"{self.base_url}/projects/{self.project_id}/repository/files/{file_path}"
        
        # Encode file path
        encoded_file_path = file_path.replace("/", "%2F")
        url = f"{self.base_url}/projects/{self.project_id}/repository/files/{encoded_file_path}"
        
        # Prepare data
        data = {
            "branch": branch,
            "content": content,
            "commit_message": commit_message
        }
        
        # Check if file exists
        try:
            self.get_file_content(file_path, branch)
            # File exists, update it
            response = requests.put(url, headers=self.headers, data=data)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                # File doesn't exist, create it
                response = requests.post(url, headers=self.headers, data=data)
            else:
                raise
        
        response.raise_for_status()
        return response.json()
    
    def create_merge_request(self, title: str, description: str, source_branch: str, target_branch: str = "main") -> Dict[str, Any]:
        """
        Create a merge request.
        
        Args:
            title: Title of the merge request
            description: Description of the merge request
            source_branch: Source branch name
            target_branch: Target branch name
            
        Returns:
            Merge request information
        """
        url = f"{self.base_url}/projects/{self.project_id}/merge_requests"
        data = {
            "title": title,
            "description": description,
            "source_branch": source_branch,
            "target_branch": target_branch
        }
        response = requests.post(url, headers=self.headers, data=data)
        response.raise_for_status()
        return response.json()


class VersionControlManager:
    """
    Manager for version control operations.
    """
    
    def __init__(self, provider: str = "github"):
        """
        Initialize the version control manager.
        
        Args:
            provider: Version control provider (github or gitlab)
        """
        self.provider = provider.lower()
        
        if self.provider == "github":
            self.client = GitHubClient()
        elif self.provider == "gitlab":
            self.client = GitLabClient()
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def create_feature_branch(self, feature_name: str) -> Dict[str, Any]:
        """
        Create a new feature branch.
        
        Args:
            feature_name: Name of the feature
            
        Returns:
            Result of branch creation
        """
        # Sanitize and enforce feature/<id> naming
        sanitized = feature_name.lower().replace(' ', '-')
        if not sanitized.startswith('feature/'):
            branch_name = f"feature/{sanitized}"
        else:
            branch_name = sanitized
        return self.client.create_branch(branch_name)
    
    def commit_code_changes(self, files: Dict[str, str], commit_message: str, branch: str) -> List[Dict[str, Any]]:
        """
        Commit code changes to a branch.
        
        Args:
            files: Dictionary mapping file paths to content
            commit_message: Commit message
            branch: Branch name
            
        Returns:
            List of results for each file
        """
        results = []
        
        for file_path, content in files.items():
            result = self.client.create_or_update_file(file_path, content, commit_message, branch)
            results.append(result)
        
        return results
    
    def create_pull_request(self, title: str, description: str, feature_branch: str) -> Dict[str, Any]:
        """
        Create a pull request or merge request.
        
        Args:
            title: Title of the PR/MR
            description: Description of the PR/MR
            feature_branch: Feature branch name
            
        Returns:
            PR/MR information
        """
        if self.provider == "github":
            # Ensure head branch uses feature/<id>
            head = feature_branch if feature_branch.startswith('feature/') else f"feature/{feature_branch}"
            return self.client.create_pull_request(title, description, head)
        else:  # gitlab
            source = feature_branch if feature_branch.startswith('feature/') else f"feature/{feature_branch}"
            return self.client.create_merge_request(title, description, source)
