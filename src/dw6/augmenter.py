# src/dw6/augmenter.py

import httpx

class PromptAugmenter:
    """Augments user prompts with context from the MCP server."""

    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url

    def _get_context(self, endpoint):
        try:
            response = httpx.get(f"{self.base_url}{endpoint}")
            response.raise_for_status()
            return response.json()
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            return {"error": f"Could not fetch {endpoint}: {e}"}

    def augment_prompt(self, original_prompt):
        """Fetches context and prepends it to the prompt."""
        state_context = self._get_context("/context/state")
        git_context = self._get_context("/context/git")
        req_context = self._get_context("/context/requirements")

        context_str = (
            f"--- System Context ---\n"
            f"Workflow State: {state_context.get('CurrentStage', 'Unknown')}\n"
            f"Git Branch: {git_context.get('branch', 'Unknown')}\n"
            f"Git Commit: {git_context.get('latest_commit', 'Unknown')}\n"
            f"Git Status: {git_context.get('status', 'Unknown')}\n"
            f"Meta-Requirements: {req_context.get('requirements', [])}\n"
            f"----------------------\n\n"
        )

        return f"{context_str}User Requirement: {original_prompt}"
