# dw6/main.py
import argparse
import sys
import re
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from dw6.state_manager import WorkflowManager, STAGES
from dw6.augmenter import PromptAugmenter
from dw6.templates import process_prompt

META_LOG_FILE = Path("logs/meta_requirements.log")
TECH_DEBT_FILE = Path("logs/technical_debt.log")

def register_meta_requirement(description: str):
    """Logs a new meta-requirement to the meta_requirements.log file."""
    META_LOG_FILE.parent.mkdir(exist_ok=True)
    
    last_id = 0
    if META_LOG_FILE.exists():
        with open(META_LOG_FILE, "r") as f:
            lines = f.readlines()
            if lines:
                last_line = lines[-1]
                match = re.search(r'^\[ID:(\d+)\]', last_line)
                if match:
                    last_id = int(match.group(1))

    new_id = last_id + 1
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    log_entry = f"[ID:{new_id}] [TS:{timestamp}] {description}\n"

    with open(META_LOG_FILE, "a") as f:
        f.write(log_entry)
    
    print(f"Successfully logged meta-requirement {new_id}.")

def register_technical_debt(description, issue_type="test", commit_to_fix=None):
    """Registers a known technical debt item for future resolution."""
    TECH_DEBT_FILE.parent.mkdir(exist_ok=True)
    
    last_id = 0
    if TECH_DEBT_FILE.exists():
        with open(TECH_DEBT_FILE, "r") as f:
            lines = f.readlines()
            if lines:
                last_line = lines[-1]
                match = re.search(r'^\[ID:(\d+)\]', last_line)
                if match:
                    last_id = int(match.group(1))

    new_id = last_id + 1
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    status = "OPEN"
    log_entry = f"[ID:{new_id}] [TS:{timestamp}] [TYPE:{issue_type}] [STATUS:{status}] "
    if commit_to_fix:
        log_entry += f"[COMMIT:{commit_to_fix}] "
    log_entry += f"{description}\n"

    with open(TECH_DEBT_FILE, "a") as f:
        f.write(log_entry)
    
    print(f"Successfully logged technical debt {new_id}.")
    return new_id

def revert_to_previous_stage(manager, target_stage_name=None):
    """Reverts the workflow to the previous stage or a specified target stage."""
    current_stage = manager.current_stage
    current_index = STAGES.index(current_stage)

    if target_stage_name:
        if target_stage_name not in STAGES:
            print(f"Error: Invalid target stage '{target_stage_name}'.", file=sys.stderr)
            sys.exit(1)
        target_index = STAGES.index(target_stage_name)
    else:
        target_index = current_index - 1

    if current_index == 0:
        print("Info: Already at the first stage ('Engineer'). Cannot revert further.", file=sys.stdout)
        sys.exit(0)

    if target_index < 0:
        print("Error: Cannot revert past the first stage.", file=sys.stderr)
        sys.exit(1)

    target_stage = STAGES[target_index]

    if target_index > current_index:
        print(f"Error: Cannot revert forward from {current_stage} to {target_stage}.")
        print(f"Use 'approve' to move forward in the workflow.")
        return

    print(f"Reverting from {current_stage} to {target_stage}...")
    manager.state.set("CurrentStage", target_stage)
    manager.state.save()
    print(f"Successfully reverted to {target_stage} stage.")

def main():
    """Main entry point for the DW6 CLI."""
    parser = argparse.ArgumentParser(description="DW6 Workflow Management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands", required=True)

    # Approve command
    approve_parser = subparsers.add_parser("approve", help="Approve the current stage and advance to the next.")
    approve_parser.add_argument("--with-tech-debt", action="store_true", help="Approve the stage even with validation failures, logging them as technical debt.")

    # New command
    new_parser = subparsers.add_parser("new", help="Create a new requirement specification from a prompt.")
    new_parser.add_argument("prompt", type=str, help="The high-level user prompt.")

    # Meta-req command
    meta_req_parser = subparsers.add_parser("meta-req", help="Register a new meta-requirement for the workflow.")
    meta_req_parser.add_argument("description", type=str, help="The description of the meta-requirement.")

    # Tech-debt command
    tech_debt_parser = subparsers.add_parser("tech-debt", help="Register a technical debt item.")
    tech_debt_parser.add_argument("description", type=str, help="Description of the technical debt.")
    tech_debt_parser.add_argument("--type", default="test", help="Type of technical debt (e.g., test, code, deployment)")
    tech_debt_parser.add_argument("--commit", help="Commit hash where this should be fixed")

    # Revert command
    revert_parser = subparsers.add_parser("revert", help="Revert to a previous workflow stage.")
    revert_parser.add_argument("--to", dest="target_stage", help="Target stage to revert to. Defaults to previous stage.")

    # Do command
    do_parser = subparsers.add_parser("do", help="Execute a governed action.")
    do_parser.add_argument("action", type=str, help="The action to execute.")

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()
    manager = WorkflowManager()
    
    if args.command == "meta-req":
        register_meta_requirement(args.description)
    elif args.command == "tech-debt":
        register_technical_debt(args.description, args.type, args.commit)
    elif args.command == "revert":
        revert_to_previous_stage(manager, args.target_stage)
    elif args.command == "do":
        try:
            manager.governor.authorize(args.action)
            # The command is authorized. The gatekeeper's job is done.
        except PermissionError:
            sys.exit(1)
    elif args.command == "approve":
        manager.approve(with_tech_debt=args.with_tech_debt)
    elif args.command == "new":
        augmenter = PromptAugmenter()
        augmented_prompt = augmenter.augment_prompt(args.prompt)
        process_prompt(augmented_prompt)

if __name__ == "__main__":
    main()
