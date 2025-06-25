# Requirement: 6

## 1. High-Level Goal

### System Context

- Workflow State: Unknown
- Git Branch: Unknown
- Git Commit: Unknown
- Git Status: Unknown
- Meta-Requirements: []

User Requirement: Implement a Protocol Kernel Locking System to prevent unauthorized modifications to core workflow files like state_manager.py and git_handler.py. The system should allow changes only through a formal, audited 'unlock' and 'lock' process.

## 2. Guiding Principles

**Working Philosophy:** We always look to granularize projects into small, atomic requirements and sub-requirements. The more granular the requirement, the easier it is to scope, implement, test, and validate. This iterative approach minimizes risk and ensures steady, verifiable progress.

## 3. Proposed Implementation

This system will be implemented using file system permissions, controlled by new CLI commands, and configured via the project's `pyproject.toml`.

### a. Configuration

The list of protected kernel files will be defined in `pyproject.toml`:

```toml
[tool.dw6]
# ... other settings

kernel_files = [
    "src/dw6/state_manager.py",
    "src/dw6/git_handler.py",
    "src/dw6/main.py"
]
```

### b. Locking Mechanism

The locking will be achieved by modifying file permissions:

- **Locked:** Files will be set to read-only (permission `444`).
- **Unlocked:** Files will be set to read-write (permission `644`).

This provides a simple and robust OS-level protection against accidental edits.

### c. New CLI Commands

Two new commands will be added to `dw6/main.py`:

1. **`dw6 kernel-lock`**
    - Reads the `kernel_files` list from `pyproject.toml`.
    - Iterates through the list, setting each file's permission to read-only.
    - Logs the action to `logs/audit.log`.

2. **`dw6 kernel-unlock`**
    - Requires a confirmation flag to prevent accidental use: `dw6 kernel-unlock --i-am-sure`.
    - If the flag is present, it sets the kernel files to read-write.
    - Logs the action to `logs/audit.log`.

### d. Auditing

A new log file, `logs/audit.log`, will be created. All lock and unlock events will be appended to this file with a timestamp, providing a clear audit trail.

Example `logs/audit.log`:

```log
2025-06-26T06:10:00Z - KERNEL UNLOCKED by user: ubuntu
2025-06-26T06:15:30Z - KERNEL LOCKED by user: ubuntu
```

## 4. Acceptance Criteria

- After running `dw6 kernel-lock`, any attempt to save changes to a file in the `kernel_files` list from an editor should fail due to read-only permissions.
- The `dw6 kernel-unlock --i-am-sure` command must successfully make the files writable again.
- Each lock/unlock operation must generate a corresponding entry in `logs/audit.log`.
- The system must correctly read the list of files to protect from `pyproject.toml`.
