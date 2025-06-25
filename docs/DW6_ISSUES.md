# DW6 Protocol Issues - Cycle 1 Evaluation

This document tracks issues, flaws, and potential improvements discovered during the evaluation of the DW6 protocol.

## 1. Environment Setup and Dependency Installation

- **Issue:** The virtual environment (`venv`) creation and/or the installation of project dependencies via `pip install -e .[test]` is not robust. The user reported that the environment was not created and dependencies were missing.
- **Impact:** Critical. The project is not usable out-of-the-box, which defeats the purpose of an automated setup workflow.
- **Resolution (in `dw6_test_bed_v5`):** Replaced `python -m venv` and `pip` with `uv` for environment creation and dependency installation (`uv venv` and `uv pip install`). This proved to be fast, reliable, and solved the issue completely.

## 2. GitHub Integration & Automation

- **Issue:** The original workflow required manual steps for creating a GitHub repository and linking it to the local project.
- **Impact:** Poor user experience, redundancy, and a barrier to full automation.
- **Resolution (in `dw6_test_bed_v5`):** Used the `github-mcp-server` to programmatically create the repository and link it using the user's stored credentials. This fully automated the repository setup.

## 3. Programmatic GitHub Authentication

- **Issue:** The workflow triggered a UI-based authentication prompt for GitHub operations (`git push`). This breaks the command-line-native experience and prevents full automation.
- **Impact:** Prevents unattended execution of the workflow and requires manual intervention.
- **Resolution (in `dw6_test_bed_v5`):** The `github-mcp-server` uses a stored Personal Access Token (PAT), and the `git push` command was constructed to include the PAT in the remote URL, automating authentication seamlessly.

## 4. Broken `status` Command

- **Issue:** The `dw6 status` command failed with an `AttributeError: 'WorkflowManager' object has no attribute 'get_status'`.
- **Impact:** Critical. The core status-checking functionality was non-operational.
- **Resolution (in `dw6_test_bed_v5`):** Corrected the method call in `src/dw6/cli.py` from `manager.get_status()` to `manager.get_state()`.

## 5. Silent `status` Command

- **Issue:** After fixing the `AttributeError`, the `dw6 status` command executed silently, providing no output to the user.
- **Impact:** High. The command failed to provide any information about the workflow's state.
- **Resolution (in `dw6_test_bed_v5`):** Modified `src/dw6/cli.py` to iterate through the dictionary returned by `manager.get_state()` and print each key-value pair, providing clear and informative output.

## 6. `engineer start` Command Fails with KeyError

- **Issue:** The `dw6 engineer start` command failed with a `KeyError: 'Cycle'` because it was trying to access a non-existent key in the state dictionary.
- **Impact:** Critical. It was impossible to generate the technical specification, blocking the workflow.
- **Resolution (in `dw6_test_bed_v5`):** Corrected the key access in `src/dw6/cli.py` from `state['Cycle']` to the correct key, `state['RequirementPointer']`.

## 7. Confusing Approval Message

- **Issue:** The `approve` command printed a confusing success message, such as `--- Stage Researcher Approved. New Stage: Researcher ---`.
- **Impact:** Low, but the message is misleading and unprofessional.
- **Resolution (in `dw6_test_bed_v5`):** Fixed the log message in `src/dw6/state_manager.py` to correctly report the stage that was just completed (e.g., `--- Stage Engineer Approved. New Stage: Researcher ---`).
