# DW6 Improvement Protocol: Towards a Deterministic and Robust Workflow

## 1. Problem Statement

The DW6 workflow, in its current implementation, suffers from critical flaws that undermine its core principles. The AI agent has demonstrated an ability to operate subjectively, fail to register meta-requirements, and bypass the intended stage progression (e.g., jumping from `Engineer` to `Coder`). This leads to an unreliable, non-deterministic, and weak workflow. This document outlines the formal requirements to address these failures and forge a robust, predictable, and strictly-enforced development protocol.

## 2. Core Principles for Remediation

1. **Determinism:** The workflow must proceed in a predictable, non-subjective manner. The AI's next action on the protocol level must be determined by the system's state, not the AI's discretion.
2. **Strict Stage Enforcement:** Each stage (`Engineer`, `Coder`, `Validator`, `Deployer`) must have clear entry and exit criteria. The AI's capabilities must be dynamically locked to the active stage. No stage can be skipped.
3. **Immutable Requirement Log:** All tasks, whether for the project or the workflow itself, must be registered as formal, atomic requirements in an immutable log before work can begin.
4. **System-Driven Progression:** The system, not the AI, decides when a stage is complete based on the fulfillment of exit criteria. The `approve` command will be a request for validation, not a command for progression.

## 3. Actionable Requirements

This section lists the formal, granular requirements that will be implemented sequentially to address the problems. Each requirement will be implemented in its own complete DW6 cycle.

- **REQ-M1: The State Machine Governor.**
  - **Description:** Implement a `Governor` class within the `state_manager.py` module. This class will be the single authority on stage transitions. The `dw6 approve` command will now send a request to the `Governor`. The `Governor` will only approve the transition if all exit criteria for the current stage are met (e.g., for the `Engineer` stage, a technical specification file must exist).
  - **Acceptance Criteria:** The `dw6 approve` command fails with an explicit error if the current stage's exit criteria are not met.

- **REQ-M2: Stage-Locked AI Behavior via Embedded Rules.**
  - **Description:** To prevent file system permission issues and create a more robust, self-contained system, the stage-locking rules will be embedded directly into the `Governor` class. A dictionary within the `Governor` will map each stage (`Engineer`, `Coder`, `Validator`, `Deployer`, `Researcher`) to a set of permissible actions. Upon entering a new stage, the `Governor` will enforce these rules internally, blocking any unauthorized AI actions.
  - **Acceptance Criteria:** An attempt by the AI to perform an action not explicitly permitted by the `Governor`'s internal rule set for the current stage results in a hard failure.

- **REQ-M3: Formal Meta-Requirement Log.**
  - **Description:** Create a new CLI command, `dw6 meta-req "<description>"`, to allow the user to formally register an improvement requirement for the DW6 protocol itself. This command will append the requirement to a new, simple, append-only log file named `meta_requirements.log`. The system will be designed to process these requirements sequentially.
  - **Acceptance Criteria:** Running the `dw6 meta-req` command adds a new, timestamped, and uniquely identified requirement to the `meta_requirements.log`.
