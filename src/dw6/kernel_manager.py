# dw6/kernel_manager.py
# This is a test comment.
import os
import stat
import toml
from pathlib import Path
from datetime import datetime, timezone

AUDIT_LOG_FILE = Path("logs/audit.log")

class KernelManager:
    """Manages the locking and unlocking of protocol kernel files."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.pyproject_path = project_root / "pyproject.toml"
        self.kernel_files = self._load_kernel_files()

    def _load_kernel_files(self) -> list[Path]:
        """Loads the list of kernel files from pyproject.toml."""
        if not self.pyproject_path.exists():
            raise FileNotFoundError("pyproject.toml not found in the project root.")
        
        config = toml.load(self.pyproject_path)
        file_paths_str = config.get("tool", {}).get("dw6", {}).get("kernel_files", [])
        
        if not file_paths_str:
            print("Warning: No kernel_files defined in pyproject.toml under [tool.dw6]")
            return []

        return [self.project_root / path for path in file_paths_str]

    def _log_audit_event(self, event: str):
        """Logs an event to the audit log."""
        AUDIT_LOG_FILE.parent.mkdir(exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat()
        user = os.getenv("USER", "unknown")
        log_entry = f"{timestamp} - {event} by user: {user}\n"
        
        with open(AUDIT_LOG_FILE, "a") as f:
            f.write(log_entry)

    def lock(self):
        """Sets kernel files to read-only."""
        print("--- Locking Protocol Kernel Files ---")
        for file_path in self.kernel_files:
            if file_path.exists():
                os.chmod(file_path, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH) # Read-only (444)
                print(f"  - Locked: {file_path.relative_to(self.project_root)}")
            else:
                print(f"  - Warning: Not found, skipping: {file_path.relative_to(self.project_root)}")
        self._log_audit_event("KERNEL LOCKED")
        print("--- Kernel Locked ---")

    def unlock(self):
        """Sets kernel files to read-write."""
        print("--- Unlocking Protocol Kernel Files ---")
        for file_path in self.kernel_files:
            if file_path.exists():
                os.chmod(file_path, stat.S_IWRITE | stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH) # Read-write (644)
                print(f"  - Unlocked: {file_path.relative_to(self.project_root)}")
            else:
                print(f"  - Warning: Not found, skipping: {file_path.relative_to(self.project_root)}")
        self._log_audit_event("KERNEL UNLOCKED")
        print("--- Kernel Unlocked ---")
