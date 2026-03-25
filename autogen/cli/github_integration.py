# Copyright (c) 2023 - 2025, clippy kernel development team
#
# SPDX-License-Identifier: Apache-2.0

"""
Experimental GitHub issue workflow for the Clippy SWE Agent.

This module currently provides scaffolded support for:
- Cloning and inspecting repositories
- Fetching issue context
- Generating proposed solutions and patches
- Heuristically running common test commands
- Optionally creating a PR when a real patch exists
"""

import json
import logging
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class GitHubIssue:
    """Represents a GitHub issue to be resolved."""

    number: int
    title: str
    body: str
    repository: str
    labels: list[str]
    assignees: list[str]


@dataclass
class PatchResult:
    """Result of patch generation."""

    success: bool
    patch_file: Path | None
    changed_files: list[str]
    tests_passed: bool
    error_message: str | None


class GitHubIntegration:
    """
    Experimental GitHub integration for issue analysis and patch scaffolding.

    This helper can clone repositories, fetch issue metadata, and ask the agent
    for analysis or proposed solutions. Automatic change application remains
    scaffolded in the current implementation.
    """

    def __init__(self, agent, github_token: str | None = None):
        """
        Initialize GitHub integration.
        
        Args:
            agent: ClippySWEAgent instance
            github_token: Optional GitHub personal access token
        """
        self.agent = agent
        self.github_token = github_token
        self.workspace = Path(tempfile.mkdtemp(prefix="clippy_gh_"))

    def resolve_issue(
        self, repository: str, issue_number: int, create_pr: bool = True
    ) -> PatchResult:
        """
        Autonomously resolve a GitHub issue.
        
        Args:
            repository: Repository in format "owner/repo"
            issue_number: Issue number to resolve
            create_pr: Whether to create a pull request
            
        Returns:
            PatchResult with resolution details
        """
        logger.info(f"Resolving issue #{issue_number} in {repository}")

        try:
            # 1. Clone repository
            repo_path = self._clone_repository(repository)
            if not repo_path:
                return PatchResult(
                    success=False,
                    patch_file=None,
                    changed_files=[],
                    tests_passed=False,
                    error_message="Failed to clone repository",
                )

            # 2. Fetch issue details
            issue = self._fetch_issue(repository, issue_number)
            if not issue:
                return PatchResult(
                    success=False,
                    patch_file=None,
                    changed_files=[],
                    tests_passed=False,
                    error_message="Failed to fetch issue",
                )

            # 3. Analyze issue and codebase
            analysis = self._analyze_issue_and_codebase(issue, repo_path)

            # 4. Generate solution
            solution = self._generate_solution(issue, analysis, repo_path)

            if not solution.get("success"):
                return PatchResult(
                    success=False,
                    patch_file=None,
                    changed_files=[],
                    tests_passed=False,
                    error_message=solution.get("error", "Solution generation failed"),
                )

            # 5. Apply changes
            changed_files = self._apply_changes(solution, repo_path)

            # 6. Run tests
            tests_passed = self._run_tests(repo_path)

            # 7. Generate patch
            patch_file = self._generate_patch(repo_path, issue_number)

            # 8. Create PR if requested
            if create_pr and patch_file and tests_passed:
                pr_url = self._create_pull_request(repository, issue, patch_file, repo_path)
                logger.info(f"Created PR: {pr_url}")

            return PatchResult(
                success=tests_passed,
                patch_file=patch_file,
                changed_files=changed_files,
                tests_passed=tests_passed,
                error_message=None if tests_passed else "Tests failed",
            )

        except Exception as e:
            logger.error(f"Issue resolution failed: {e}", exc_info=True)
            return PatchResult(
                success=False,
                patch_file=None,
                changed_files=[],
                tests_passed=False,
                error_message=str(e),
            )

    def _clone_repository(self, repository: str) -> Path | None:
        """Clone GitHub repository."""
        try:
            repo_url = f"https://github.com/{repository}.git"
            if self.github_token:
                repo_url = f"https://{self.github_token}@github.com/{repository}.git"

            repo_path = self.workspace / repository.replace("/", "_")

            result = subprocess.run(
                ["git", "clone", repo_url, str(repo_path)],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0:
                logger.info(f"Cloned repository to {repo_path}")
                return repo_path
            else:
                logger.error(f"Clone failed: {result.stderr}")
                return None

        except Exception as e:
            logger.error(f"Clone error: {e}")
            return None

    def _fetch_issue(self, repository: str, issue_number: int) -> GitHubIssue | None:
        """Fetch issue details from GitHub."""
        try:
            # Use gh CLI if available
            result = subprocess.run(
                ["gh", "issue", "view", str(issue_number), "--repo", repository, "--json", "number,title,body,labels"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                return GitHubIssue(
                    number=data["number"],
                    title=data["title"],
                    body=data["body"],
                    repository=repository,
                    labels=[label["name"] for label in data.get("labels", [])],
                    assignees=[],
                )
            else:
                logger.warning("gh CLI not available, using mock issue")
                return GitHubIssue(
                    number=issue_number,
                    title=f"Issue #{issue_number}",
                    body="Issue details not available",
                    repository=repository,
                    labels=[],
                    assignees=[],
                )

        except Exception as e:
            logger.error(f"Failed to fetch issue: {e}")
            return None

    def _analyze_issue_and_codebase(self, issue: GitHubIssue, repo_path: Path) -> dict[str, Any]:
        """Analyze the issue and codebase context."""
        analysis_task = f"""
        Analyze this GitHub issue and the codebase to understand the problem:
        
        **Issue #{issue.number}: {issue.title}**
        {issue.body}
        
        **Repository**: {issue.repository}
        **Labels**: {', '.join(issue.labels)}
        
        **Your task:**
        1. Understand the issue thoroughly
        2. Identify relevant files and code sections
        3. Determine the root cause
        4. Propose a solution approach
        
        Repository is located at: {repo_path}
        """

        result = self.agent.execute_task(
            task_description=analysis_task,
            task_type="research",
            context={"repository_path": str(repo_path), "issue_number": issue.number},
        )

        return {
            "issue": issue,
            "analysis": result.get("result", ""),
            "repository_path": repo_path,
        }

    def _generate_solution(
        self, issue: GitHubIssue, analysis: dict[str, Any], repo_path: Path
    ) -> dict[str, Any]:
        """Generate solution code for the issue."""
        solution_task = f"""
        Based on the analysis, implement a solution for this issue:
        
        **Issue #{issue.number}: {issue.title}**
        
        **Analysis:**
        {analysis['analysis']}
        
        **Requirements:**
        1. Implement the fix or feature
        2. Ensure code quality and best practices
        3. Add or update tests as needed
        4. Update documentation if necessary
        5. Provide clear commit message
        
        Repository: {repo_path}
        
        Provide the solution as file paths and their new contents.
        """

        result = self.agent.execute_task(
            task_description=solution_task,
            task_type="coding",
            context={
                "repository_path": str(repo_path),
                "issue_number": issue.number,
                "issue_title": issue.title,
            },
        )

        return result

    def _apply_changes(self, solution: dict[str, Any], repo_path: Path) -> list[str]:
        """Apply code changes to the repository.

        SCAFFOLDED: This method does NOT apply changes. It is a placeholder
        that logs intent but returns an empty list. A real implementation
        must parse the LLM solution output and write files to repo_path.
        """
        changed_files: list[str] = []

        logger.warning(
            "SCAFFOLDED: _apply_changes() is not implemented. "
            "Changes are NOT being applied to the repository."
        )

        return changed_files

    def _run_tests(self, repo_path: Path) -> bool:
        """Run tests in the repository."""
        try:
            # Try common test commands
            test_commands = [
                ["pytest"],
                ["python", "-m", "pytest"],
                ["npm", "test"],
                ["make", "test"],
                ["python", "-m", "unittest", "discover"],
            ]

            for cmd in test_commands:
                result = subprocess.run(
                    cmd,
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=300,
                )

                if result.returncode == 0:
                    logger.info(f"Tests passed with command: {' '.join(cmd)}")
                    return True

            logger.warning("No test command succeeded")
            return False

        except Exception as e:
            logger.error(f"Test execution failed: {e}", exc_info=True)
            return False

    def _generate_patch(self, repo_path: Path, issue_number: int) -> Path | None:
        """Generate a git patch file."""
        try:
            patch_file = self.workspace / f"issue_{issue_number}.patch"

            result = subprocess.run(
                ["git", "diff", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0 and result.stdout:
                with open(patch_file, "w") as f:
                    f.write(result.stdout)

                logger.info(f"Generated patch: {patch_file}")
                return patch_file
            else:
                logger.warning("No changes to create patch")
                return None

        except Exception as e:
            logger.error(f"Patch generation failed: {e}")
            return None

    def _create_pull_request(
        self, repository: str, issue: GitHubIssue, patch_file: Path, repo_path: Path
    ) -> str | None:
        """Create a pull request with the changes."""
        try:
            # Create a new branch
            branch_name = f"clippy-swe/issue-{issue.number}"

            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=repo_path,
                capture_output=True,
                timeout=30,
            )

            # Commit changes
            commit_message = f"Fix #{issue.number}: {issue.title}\n\nAutomatically generated by Clippy SWE Agent"

            subprocess.run(
                ["git", "add", "."],
                cwd=repo_path,
                capture_output=True,
                timeout=30,
            )

            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=repo_path,
                capture_output=True,
                timeout=30,
            )

            # Push branch (requires authentication)
            if self.github_token:
                subprocess.run(
                    ["git", "push", "-u", "origin", branch_name],
                    cwd=repo_path,
                    capture_output=True,
                    timeout=60,
                )

                # Create PR using gh CLI
                result = subprocess.run(
                    [
                        "gh",
                        "pr",
                        "create",
                        "--title",
                        f"Fix #{issue.number}: {issue.title}",
                        "--body",
                        f"Fixes #{issue.number}\n\nAutomatically generated by Clippy SWE Agent",
                        "--repo",
                        repository,
                    ],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                if result.returncode == 0:
                    pr_url = result.stdout.strip()
                    return pr_url

            logger.info(f"PR creation completed for branch {branch_name}")
            return f"Branch {branch_name} created"

        except Exception as e:
            logger.error(f"PR creation failed: {e}")
            return None

    def cleanup(self) -> None:
        """Clean up temporary workspace."""
        import shutil

        try:
            if self.workspace.exists():
                shutil.rmtree(self.workspace)
                logger.info(f"Cleaned up workspace: {self.workspace}")
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")
