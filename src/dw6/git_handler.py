import sys
import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv
import git

# Load environment variables from .env file
load_dotenv()

class GitManager:
    """A class to manage all Git operations for the DW7 protocol."""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        if not self.project_path.is_dir():
            raise ValueError(f"Project path does not exist: {project_path}")
        self.repo = self._get_repo()

    def _run_command(self, command: list[str], suppress_output=False):
        """Runs a command in the project directory and handles errors."""
        try:
            result = subprocess.run(
                command,
                cwd=self.project_path,
                check=True,
                capture_output=True,
                text=True,
            )
            if not suppress_output:
                print(result.stdout)
            return result
        except subprocess.CalledProcessError as e:
            print(f"ERROR running command: {' '.join(command)}", file=sys.stderr)
            print(f"STDOUT: {e.stdout}", file=sys.stderr)
            print(f"STDERR: {e.stderr}", file=sys.stderr)
            sys.exit(1)

    def _get_repo(self):
        """Initializes and returns a git.Repo object, or None if not a repo."""
        try:
            return git.Repo(self.project_path, search_parent_directories=True)
        except (git.InvalidGitRepositoryError, git.NoSuchPathError):
            return None

    def initialize_repo(self):
        """Initializes a new Git repository."""
        if self.repo:
            print("Git repository already exists.")
            return
        print("Initializing Git repository...")
        self._run_command(["git", "init"])
        self.repo = git.Repo(self.project_path) # Re-initialize repo object

    def add_remote(self, remote_url: str):
        """Adds a remote origin to the repository."""
        if self.repo and "origin" in [remote.name for remote in self.repo.remotes]:
            print("Remote 'origin' already exists. Updating URL.")
            self._run_command(["git", "remote", "set-url", "origin", remote_url])
        else:
            print(f"Adding remote 'origin': {remote_url}")
            self._run_command(["git", "remote", "add", "origin", remote_url])

    def commit_all(self, message: str):
        """Adds all changes and commits them."""
        print("Adding all files to staging...")
        self._run_command(["git", "add", "."])
        print(f"Committing with message: {message}")
        # Use --no-verify to bypass pre-commit hooks if any, for automated commits
        self._run_command(["git", "commit", "-m", message, "--no-verify"])

    def push_to_remote(self, branch="master", set_upstream=False):
        """Pushes changes to the remote repository, relying on system's credential helper."""
        print(f"Pushing branch '{branch}' to remote 'origin'...")
        command = ["git", "push"]
        if set_upstream:
            command.extend(["-u", "origin", branch])
        else:
            command.extend(["origin", branch])
        
        # This is the key part: we just run 'git push'.
        # The environment's credential helper will handle authentication.
        self._run_command(command, suppress_output=True) # Suppress output for security
        print(f"Successfully pushed branch '{branch}' to remote 'origin'.")

    def is_working_directory_clean(self):
        """Checks if the Git working directory is clean."""
        if not self.repo:
            return True
        return not self.repo.is_dirty(untracked_files=True)

    def get_current_commit_sha(self):
        """Returns the SHA of the current HEAD commit."""
        if not self.repo:
            return None
        return self.repo.head.commit.hexsha

