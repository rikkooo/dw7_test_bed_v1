# Coder Stage Deliverable

Changes between 378a725 and 6e7702d

## Changed Files

- `logs/workflow_state.txt`
- `src/dw6/main.py`
- `src/dw6/state_manager.py`

## Diff

```diff
diff --git a/logs/workflow_state.txt b/logs/workflow_state.txt
index 1de8476..293662a 100644
--- a/logs/workflow_state.txt
+++ b/logs/workflow_state.txt
@@ -1,2 +1,3 @@
 CurrentStage=Coder
 RequirementPointer=6
+LastCommitSHA_pre_transition=378a7253a5f9524b7d321a58066a805da5e11c89
diff --git a/src/dw6/main.py b/src/dw6/main.py
index c261995..5e50858 100644
--- a/src/dw6/main.py
+++ b/src/dw6/main.py
@@ -275,16 +275,6 @@ def main():
         except PermissionError:
             sys.exit(1)
     elif args.command == "approve":
-        # First, commit all changes with a standardized message
-        print("--- Committing all changes before approval ---")
-        current_stage = manager.get_state().get("CurrentStage")
-        commit_message = f"feat: Finalize work for {current_stage} stage"
-        
-        git_manager = GitManager(str(Path.cwd()))
-        git_manager.commit_all(commit_message)
-        print("--- Committing complete ---")
-
-        # Now, proceed with the approval process
         manager.approve(next_stage=args.next_stage, with_tech_debt=args.with_tech_debt)
     elif args.command == "new":
         augmenter = PromptAugmenter()
diff --git a/src/dw6/state_manager.py b/src/dw6/state_manager.py
index 6044117..3a8265f 100644
--- a/src/dw6/state_manager.py
+++ b/src/dw6/state_manager.py
@@ -89,6 +89,14 @@ class Governor:
         workflow_manager = WorkflowManager() # We still need access to its methods for now.
         workflow_manager._validate_stage(allow_failures=with_tech_debt)
         workflow_manager._run_pre_transition_actions()
+
+        # Commit all changes before finalizing the transition
+        print("--- Governor: Committing all changes ---")
+        commit_message = f"feat: Finalize work for {old_stage} stage"
+        git_manager = git_handler.GitManager(str(Path.cwd()))
+        git_manager.commit_all(commit_message)
+        print("--- Governor: Committing complete ---")
+
         self._transition_to_next_stage(next_stage) # This method now belongs to the Governor
         workflow_manager._run_post_transition_actions(old_stage)
         self.state.save()

```