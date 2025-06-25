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
            # Ensure the environment for the subprocess is clean and correct
            env = os.environ.copy()
            result = subprocess.run(
                command,
                cwd=self.project_path,
                check=True,
                capture_output=True,
                text=True,
                env=env
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
        """Adds all changes and commits them, handling the 'nothing to commit' case."""
        print("Adding all files to staging...")
        self._run_command(["git", "add", "."])

        print(f"Attempting to commit with message: {message}")
        command = ["git", "commit", "-m", message, "--no-verify"]
        
        # Run commit command directly to handle specific exit codes
        result = subprocess.run(
            command,
            cwd=self.project_path,
            capture_output=True,
            text=True,
            env=os.environ.copy()
        )

        if result.returncode == 0:
            # Successful commit
            print(result.stdout)
        elif result.returncode == 1 and ("nothing to commit" in result.stdout or "no changes added to commit" in result.stdout):
            # This is an expected state, not an error.
            print("Working directory is clean. Nothing to commit.")
        else:
            # A real error occurred.
            print(f"ERROR running command: {' '.join(command)}", file=sys.stderr)
            print(f"Return Code: {result.returncode}", file=sys.stderr)
            print(f"STDOUT: {result.stdout}", file=sys.stderr)
            print(f"STDERR: {result.stderr}", file=sys.stderr)
            sys.exit(1)

    def get_changes(self, previous_commit_sha):
        """Returns changed files and diff since a specific commit."""
        if not previous_commit_sha:
            return [], ""
        try:
            changed_files_str = self._run_command(["git", "diff", "--name-only", previous_commit_sha, "HEAD"]).stdout.strip()
            changed_files = changed_files_str.split('\n') if changed_files_str else []

            diff_str = self._run_command(["git", "diff", previous_commit_sha, "HEAD"]).stdout
            return changed_files, diff_str
        except subprocess.CalledProcessError as e:
            print(f"Error getting changes: {e}", file=sys.stderr)
            return [], ""

    def _get_authenticated_url(self):
        """Constructs an authenticated URL for the 'origin' remote."""
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            print("ERROR: GITHUB_TOKEN environment variable not set.", file=sys.stderr)
            print("Please create a .env file in the project root with GITHUB_TOKEN=<your_token>", file=sys.stderr)
            sys.exit(1)

        if "origin" not in self.repo.remotes:
            print("ERROR: Remote 'origin' not found.", file=sys.stderr)
            sys.exit(1)
        
        remote_url = self.repo.remotes.origin.url
        
        # Use the 'x-access-token' convention for PATs
        auth_url = remote_url.replace("https://", f"https://x-access-token:{token}@")
        return auth_url

    def get_current_commit_sha(self):
        """Returns the SHA of the current HEAD commit."""
        try:
            return self._run_command(["git", "rev-parse", "HEAD"]).stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Error getting current commit SHA: {e}", file=sys.stderr)
            return None

    def push_to_remote(self, branch="master", set_upstream=False):
        """Pushes changes to the remote repository using a temporarily authenticated URL."""
        print(f"Pushing branch '{branch}' to remote 'origin'...")
        
        authenticated_url = self._get_authenticated_url()
        original_url = self.repo.remotes.origin.url

        try:
            # Temporarily set the remote URL to the authenticated version
            self._run_command(["git", "remote", "set-url", "origin", authenticated_url], suppress_output=True)
            
            # Now, push using the standard 'origin' remote
            command = ["git", "push"]
            if set_upstream:
                command.extend(["-u", "origin", branch])
            
            self._run_command(command, suppress_output=True)
            print(f"Successfully pushed branch '{branch}' to remote 'origin'.")
            
        finally:
            # CRITICAL: Always change the remote URL back to the original, unauthenticated version
            self._run_command(["git", "remote", "set-url", "origin", original_url], suppress_output=True)
            print("Restored original remote URL.")

    def is_working_directory_clean(self):
        """Checks if the Git working directory is clean."""
        if not self.repo:
            return True
        return not self.repo.is_dirty(untracked_files=True)
