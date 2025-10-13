#!/usr/bin/env python3
"""
GitHub File Fetcher - Fetch specific files from GitHub without cloning
-----------------------------------------------------------------------
Uses GitHub API to fetch only the files needed for analysis, avoiding
the need to clone large repositories.
"""

import os
import base64
import requests
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from urllib.parse import urlparse


class GitHubFetcher:
    """Fetch specific files from GitHub repositories using API"""

    def __init__(self, repo_url: str, verbose: bool = False):
        """
        Initialize GitHub fetcher

        Args:
            repo_url: GitHub repository URL
            verbose: Enable verbose logging
        """
        self.repo_url = repo_url
        self.verbose = verbose
        self.owner, self.repo = self._parse_repo_url(repo_url)
        self.api_base = "https://api.github.com"
        self.github_token = os.getenv("GITHUB_TOKEN")  # Optional, for rate limiting

    def log(self, message: str):
        """Log message if verbose mode is enabled"""
        if self.verbose:
            print(f"[GitHubFetcher] {message}")

    def _parse_repo_url(self, url: str) -> Tuple[str, str]:
        """
        Parse GitHub repository URL to extract owner and repo name

        Args:
            url: GitHub URL like https://github.com/owner/repo

        Returns:
            Tuple of (owner, repo_name)
        """
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')

        if len(path_parts) >= 2:
            owner = path_parts[0]
            repo = path_parts[1].replace('.git', '')
            return owner, repo

        raise ValueError(f"Invalid GitHub URL: {url}")

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for GitHub API requests"""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitCloud-Analyzer"
        }

        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"

        return headers

    def fetch_file(self, file_path: str, default_branch: str = "main") -> Optional[str]:
        """
        Fetch a single file from the repository

        Args:
            file_path: Path to file in repository (e.g., "README.md")
            default_branch: Branch to fetch from (default: "main")

        Returns:
            File content as string, or None if file doesn't exist
        """
        url = f"{self.api_base}/repos/{self.owner}/{self.repo}/contents/{file_path}"
        params = {"ref": default_branch}

        try:
            self.log(f"Fetching {file_path}...")
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                # GitHub API returns base64 encoded content
                if 'content' in data:
                    content = base64.b64decode(data['content']).decode('utf-8', errors='ignore')
                    self.log(f"Successfully fetched {file_path} ({len(content)} bytes)")
                    return content

            elif response.status_code == 404:
                self.log(f"File not found: {file_path}")
                return None
            else:
                self.log(f"Failed to fetch {file_path}: HTTP {response.status_code}")
                return None

        except Exception as e:
            self.log(f"Error fetching {file_path}: {e}")
            return None

    def get_default_branch(self) -> str:
        """
        Get the default branch name for the repository

        Returns:
            Default branch name (e.g., "main" or "master")
        """
        url = f"{self.api_base}/repos/{self.owner}/{self.repo}"

        try:
            response = requests.get(url, headers=self._get_headers(), timeout=10)

            if response.status_code == 200:
                data = response.json()
                branch = data.get('default_branch', 'main')
                self.log(f"Default branch: {branch}")
                return branch
            else:
                self.log(f"Failed to get repo info, using 'main' as default")
                return "main"

        except Exception as e:
            self.log(f"Error getting default branch: {e}")
            return "main"

    def list_directory(self, dir_path: str = "", default_branch: str = "main") -> List[Dict]:
        """
        List files in a directory

        Args:
            dir_path: Path to directory (empty string for root)
            default_branch: Branch to fetch from

        Returns:
            List of file/directory info dicts
        """
        url = f"{self.api_base}/repos/{self.owner}/{self.repo}/contents/{dir_path}"
        params = {"ref": default_branch}

        try:
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=10)

            if response.status_code == 200:
                return response.json()
            else:
                self.log(f"Failed to list directory {dir_path}: HTTP {response.status_code}")
                return []

        except Exception as e:
            self.log(f"Error listing directory {dir_path}: {e}")
            return []

    def fetch_analysis_files(self, output_dir: Optional[str] = None) -> Dict[str, str]:
        """
        Fetch all files needed for project analysis

        Args:
            output_dir: Optional directory to save files to

        Returns:
            Dict mapping file names to their contents
        """
        # Get default branch first
        default_branch = self.get_default_branch()

        # List of key files to fetch
        key_files = [
            # README files
            'README.md',
            'README.rst',
            'README.txt',
            'README',
            'readme.md',

            # Python
            'requirements.txt',
            'setup.py',
            'pyproject.toml',
            'Pipfile',
            'conda.yml',
            'environment.yml',
            'requirements-dev.txt',
            'requirements-ml.txt',

            # Node.js
            'package.json',
            'package-lock.json',
            'yarn.lock',
            'pnpm-lock.yaml',

            # Go
            'go.mod',
            'go.sum',

            # Rust
            'Cargo.toml',
            'Cargo.lock',

            # Java
            'pom.xml',
            'build.gradle',
            'build.gradle.kts',

            # PHP
            'composer.json',

            # Ruby
            'Gemfile',
            'Gemfile.lock',

            # Docker
            'Dockerfile',
            'docker-compose.yml',
            'docker-compose.yaml',

            # Config
            '.env.example',
            'config.yml',
            'config.yaml',
        ]

        fetched_files = {}

        for file_name in key_files:
            content = self.fetch_file(file_name, default_branch)
            if content:
                fetched_files[file_name] = content

                # Optionally save to disk
                if output_dir:
                    output_path = Path(output_dir) / file_name
                    output_path.parent.mkdir(parents=True, exist_ok=True)

                    try:
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        self.log(f"Saved {file_name} to {output_path}")
                    except Exception as e:
                        self.log(f"Error saving {file_name}: {e}")

        # Also try to detect framework-specific files from root listing
        self.log("Listing root directory to detect additional files...")
        root_files = self.list_directory("", default_branch)

        for item in root_files:
            if item['type'] == 'file':
                name = item['name']

                # Fetch additional important files
                additional_patterns = [
                    'angular.json',
                    'vue.config.js',
                    'next.config.js',
                    'nuxt.config.js',
                    'gatsby-config.js',
                    'svelte.config.js',
                    'capacitor.config.json',
                    'pubspec.yaml',
                    'Jenkinsfile',
                ]

                if name in additional_patterns and name not in fetched_files:
                    content = self.fetch_file(name, default_branch)
                    if content:
                        fetched_files[name] = content

                        if output_dir:
                            output_path = Path(output_dir) / name
                            try:
                                with open(output_path, 'w', encoding='utf-8') as f:
                                    f.write(content)
                            except Exception as e:
                                self.log(f"Error saving {name}: {e}")

        self.log(f"Successfully fetched {len(fetched_files)} files")
        return fetched_files

    def check_directory_exists(self, dir_path: str, default_branch: str = "main") -> bool:
        """
        Check if a directory exists in the repository

        Args:
            dir_path: Path to directory
            default_branch: Branch to check

        Returns:
            True if directory exists
        """
        files = self.list_directory(dir_path, default_branch)
        return len(files) > 0


def fetch_github_files(repo_url: str, output_dir: Optional[str] = None, verbose: bool = False) -> Dict[str, str]:
    """
    Convenience function to fetch analysis files from a GitHub repository

    Args:
        repo_url: GitHub repository URL
        output_dir: Optional directory to save files to
        verbose: Enable verbose logging

    Returns:
        Dict mapping file names to their contents
    """
    fetcher = GitHubFetcher(repo_url, verbose=verbose)
    return fetcher.fetch_analysis_files(output_dir)
