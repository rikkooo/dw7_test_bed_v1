import re
import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from dw6 import git_handler

MASTER_FILE = "docs/WORKFLOW_MASTER.md"
REQUIREMENTS_FILE = "docs/PROJECT_REQUIREMENTS.md"
APPROVAL_FILE = "logs/approvals.log"
STAGES = ["Engineer", "Researcher", "Coder", "Validator", "Deployer"]
DELIVERABLE_PATHS = {
    "Engineer": "deliverables/engineering",
    "Coder": "deliverables/coding",
    "Validator": "deliverables/testing",
    "Deployer": "deliverables/deployment",
    "Researcher": "deliverables/research",
}

class Governor:
    RULES = {
        "Engineer": [
            "uv run python -m dw6.main new",
            "uv run python -m dw6.main meta-req",
            "ls",
            "cat",
            "view_file_outline"
        ],
        "Coder": [
            "replace_file_content",
            "write_to_file",
            "view_file_outline",
            "ls",
            "mkdir"
        ],
        "Validator": [
            "uv run pytest"
        ],
        "Deployer": [
            "git add",
            "git commit",
            "git tag",
            "uv run python -m dw6.main approve"
        ],
        "Researcher": [
            "search_web",
            "read_url_content",
            "write_to_file",
            "replace_file_content",
            "view_file_outline",
            "cat",
            "ls"
        ]
    }

    def __init__(self, state):
        self.state = state
        self.current_stage = self.state.get("CurrentStage")

    def authorize(self, command: str):
        """Checks if a command is allowed in the current stage."""
        allowed_commands = self.RULES.get(self.current_stage, [])
        if not any(command.startswith(prefix) for prefix in allowed_commands):
            error_msg = f"[GOVERNOR] Action denied. The command '{(command)}' is not allowed in the '{self.current_stage}' stage."
            print(error_msg, file=sys.stderr)
            raise PermissionError(error_msg)
        print(f"[GOVERNOR] Action authorized for stage '{self.current_stage}'.")

    def enforce_rules(self):
        rules = self.RULES.get(self.current_stage, ["No specific rules defined."])
        print(f"--- Governor: Enforcing Rules for Stage: {self.current_stage} ---")
        print("[RULE] Allowed command prefixes:")
        for rule in rules:
            print(f"  - {rule}")

    def approve(self, with_tech_debt=False):
        old_stage = self.current_stage
        print(f"--- Governor: Received Approval Request for Stage: {old_stage} ---")
        self.enforce_rules()
        self._validate_stage_exit_criteria(with_tech_debt)
        # The original logic from WorkflowManager is now fully integrated here.
        workflow_manager = WorkflowManager() # We still need access to its methods for now.
        workflow_manager._validate_stage(allow_failures=with_tech_debt)
        workflow_manager._run_pre_transition_actions()
        self._transition_to_next_stage() # This method now belongs to the Governor
        workflow_manager._run_post_transition_actions()
        self.state.save()
        print(f"--- Governor: Stage {old_stage} Approved. New Stage: {self.state.get('CurrentStage')} ---")

    def _validate_stage_exit_criteria(self, allow_failures=False):
        print(f"Governor: Validating exit criteria for stage: {self.current_stage}")
        if self.current_stage == "Engineer":
            req_id = self.state.get("RequirementPointer")
            spec_file = Path(f"deliverables/engineering/cycle_{req_id}_technical_specification.md")
            if not spec_file.exists():
                msg = f"ERROR: Exit criteria for 'Engineer' not met. Specification file not found: {spec_file}"
                if allow_failures:
                    print(f"WARNING: {msg}")
                    return False
                print(msg, file=sys.stderr)
                sys.exit(1)
            print("Governor: 'Engineer' exit criteria met.")
        elif self.current_stage == "Researcher":
            req_id = self.state.get("RequirementPointer")
            research_dir = Path("deliverables/research")
            research_dir.mkdir(parents=True, exist_ok=True)
            report_file = research_dir / f"cycle_{req_id}_research_report.md"
            if not report_file.exists():
                print(f"ERROR: Exit criteria for 'Researcher' not met. Research report not found: {report_file}", file=sys.stderr)
                sys.exit(1)
            print("Governor: 'Researcher' exit criteria met.")

    def _transition_to_next_stage(self):
        current_index = STAGES.index(self.current_stage)
        # After 'Deployer', the cycle is complete
        if self.current_stage == "Deployer":
            self._complete_requirement_cycle()
            self.current_stage = STAGES[0]
        else:
            self.current_stage = STAGES[current_index + 1]
        self.state.set("CurrentStage", self.current_stage)

    def _complete_requirement_cycle(self):
        req_id = int(self.state.get("RequirementPointer"))
        os.makedirs("logs", exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        with open(APPROVAL_FILE, "a") as f:
            f.write(f"Requirement {req_id} approved at {timestamp}\n")
        print(f"[INFO] Logged approval for Requirement ID {req_id}.")
        next_req_id = req_id + 1
        self.state.set("RequirementPointer", next_req_id)
        print(f"[INFO] Advanced to next requirement: {next_req_id}.")

class WorkflowManager:
    def __init__(self):
        self.state = WorkflowState()
        self.governor = Governor(self.state) # The manager now has a governor
        self.current_stage = self.state.get("CurrentStage")

    def get_state(self):
        return self.state.data

    def approve(self, with_tech_debt=False):
        # The manager now simply delegates to the governor.
        self.governor.approve(with_tech_debt=with_tech_debt)

    def approve_with_tech_debt(self):
        """Approves a stage despite known technical debt."""
        if self.current_stage != "Validator":
            print(f"ERROR: The --with-tech-debt flag can only be used in the Validator stage.")
            sys.exit(1)
        
        self.governor.approve(with_tech_debt=True)

    def _validate_stage(self, allow_failures=False):
        print("Validating stage requirements...")
        if self.current_stage == "Validator":
            if not self._validate_tests(allow_failures=allow_failures):
                if not allow_failures:
                    sys.exit(1)
                print("WARNING: Proceeding despite test failures. Technical debt has been logged.")
        elif self.current_stage == "Deployer":
            if not self._validate_deployment():
                if not allow_failures:
                    sys.exit(1)
                print("WARNING: Proceeding despite deployment validation failures. Technical debt has been logged.")
        print("Stage validation successful.")

    def _generate_coder_deliverable(self):
        print("Generating Coder deliverable...")
        changed_files, diff_string = git_handler.get_changes_since_last_commit()
        if not changed_files:
            print("No changes detected since the start of the Coder stage.")
            return
        deliverable_path = Path("deliverables/coding/coder_deliverable.md")
        deliverable_path.parent.mkdir(parents=True, exist_ok=True)
        with open(deliverable_path, "w") as f:
            f.write("# Coder Deliverable\n\n")
            f.write("## Changed Files\n\n")
            for file_path in changed_files:
                f.write(f"- `{file_path}`\n")
            f.write("\n## Git Diff\n\n")
            f.write("```diff\n")
            f.write(diff_string)
            f.write("\n```")
        print(f"Coder deliverable created at: {deliverable_path}")

    def _validate_tests(self, allow_failures=False):
        """Run test validation with optional failure tolerance."""
        print("Running test validation...")
        tests_dir = Path("tests")
        if not tests_dir.is_dir() or not any(tests_dir.glob("test_*.py")):
            msg = "ERROR: No test files found in the 'tests' directory."
            if allow_failures:
                print(f"WARNING: {msg}")
                return False
            print(msg, file=sys.stderr)
            sys.exit(1)

        try:
            # Use sys.executable to ensure we're using the python from the current venv
            python_executable = sys.executable
            collect_result = subprocess.run([python_executable, "-m", "pytest", "--collect-only"], 
                                          capture_output=True, text=True, check=True)
            
            if "no tests collected" in collect_result.stdout.lower():
                msg = "ERROR: Pytest collected no tests."
                if allow_failures:
                    print(f"WARNING: {msg}")
                    return False
                print(msg, file=sys.stderr)
                print(collect_result.stdout, file=sys.stderr)
                sys.exit(1)

            match = re.search(r"collected (\d+) items", collect_result.stdout)
            if not match or int(match.group(1)) == 0:
                msg = "ERROR: Pytest collected no tests."
                if allow_failures:
                    print(f"WARNING: {msg}")
                    return False
                print(msg, file=sys.stderr)
                print(collect_result.stdout, file=sys.stderr)
                sys.exit(1)

            print(f"Pytest collected {match.group(1)} tests. Running them now...")
            result = subprocess.run(
                [sys.executable, "-m", "pytest"],
                capture_output=True,
                text=True,
                check=False  # We check the return code manually
            )
            
            if result.returncode != 0:
                msg = "Pytest validation failed:"
                if allow_failures:
                    print(f"WARNING: {msg}")
                    print(result.stdout)
                    print(result.stderr)
                    # Log the technical debt
                    log_path = Path("logs/technical_debt.log")
                    log_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(log_path, "a") as f:
                        timestamp = datetime.now(timezone.utc).isoformat()
                        f.write(f"--- Technical Debt Logged: {timestamp} ---\n")
                        f.write(f"Stage: {self.current_stage}\n")
                        f.write(f"Requirement ID: {self.state.get('RequirementPointer')}\n")
                        f.write("Pytest Output:\n")
                        f.write(result.stdout)
                        f.write(result.stderr)
                        f.write("--- End of Log ---\n\n")
                    return False
                print(msg, file=sys.stderr)
                print(result.stdout, file=sys.stderr)
                print(result.stderr, file=sys.stderr)
                sys.exit(1)

            print("Pytest validation successful.")
            return True

        except (FileNotFoundError, subprocess.CalledProcessError):
            msg = "ERROR: pytest command not found or failed to run. Is it installed in your venv?"
            if allow_failures:
                print(f"WARNING: {msg}")
                return False
            print(msg, file=sys.stderr)
            sys.exit(1)

    def _validate_deployment(self):
        print("Validating deployment...")
        if not git_handler.is_github_token_present():
            sys.exit(1)
        latest_commit = git_handler.get_latest_commit_hash()
        all_remote_tags = git_handler.get_remote_tags_with_commits()
        if all_remote_tags is None:
            all_remote_tags = {}
        matching_tags = [tag for tag, commit in all_remote_tags.items() if commit == latest_commit]
        if not matching_tags:
            print("Warning: Could not retrieve remote tags. Falling back to local tag check.")
            local_tags = git_handler.get_local_tags_for_commit(latest_commit)
            if not local_tags:
                print(f"ERROR: The latest commit ({latest_commit[:7]}) has not been tagged.", file=sys.stderr)
                sys.exit(1)
            matching_tags = local_tags
        print(f"Deployment validation successful: Latest commit is tagged with: {', '.join(matching_tags)}.")
        print("Pushing changes to remote repository...")
        git_handler.push_to_remote()
        return True

    def _run_pre_transition_actions(self):
        pass

    def _run_post_transition_actions(self):
        if self.current_stage == "Coder":
            git_handler.save_current_commit_sha()
            changed_files, diff = git_handler.get_changes_since_last_commit()
            deliverable_path = Path(DELIVERABLE_PATHS["Coder"]) / f"{self.current_stage.lower()}_deliverable.md"
            deliverable_path.parent.mkdir(parents=True, exist_ok=True)
            with open(deliverable_path, "w") as f:
                f.write(f"# {self.current_stage} Stage Deliverable\n\n")
                f.write("## Changed Files\n\n")
                f.write("\n".join(f"- `{file}`" for file in changed_files))
                f.write("\n\n## Diff\n\n")
                f.write(f"```diff\n{diff}\n```")



class WorkflowState:
    def __init__(self):
        self.state_file = Path("logs/workflow_state.txt")
        self.data = {}
        if self.state_file.exists():
            with open(self.state_file, "r") as f:
                for line in f:
                    key, value = line.strip().split("=", 1)
                    self.data[key] = value
        else:
            self.initialize_state()

    def initialize_state(self):
        self.data = {
            "CurrentStage": "Engineer",
            "RequirementPointer": "1"
        }
        self.save()

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value):
        self.data[key] = str(value)

    def save(self):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w") as f:
            for key, value in self.data.items():
                f.write(f"{key}={value}\n")
