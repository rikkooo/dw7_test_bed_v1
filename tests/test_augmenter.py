# tests/test_augmenter.py

import pytest
import httpx
from unittest.mock import MagicMock
from src.dw6.augmenter import PromptAugmenter

@pytest.fixture
def mock_httpx_get(mocker):
    """Fixture to mock httpx.get calls."""
    mock = mocker.patch('httpx.get')
    
    def get_side_effect(url):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        if "/context/state" in url:
            mock_response.json.return_value = {"CurrentStage": "Coder"}
        elif "/context/git" in url:
            mock_response.json.return_value = {"branch": "feature-branch", "latest_commit": "abc1234", "status": "clean"}
        elif "/context/requirements" in url:
            mock_response.json.return_value = {"requirements": ["req1", "req2"]}
        else:
            mock_response.json.return_value = {"error": "Not Found"}
        return mock_response

    mock.side_effect = get_side_effect
    return mock

def test_augment_prompt(mock_httpx_get):
    """Tests that the prompt is correctly augmented with context."""
    augmenter = PromptAugmenter()
    original_prompt = "Implement a new login feature."

    augmented_prompt = augmenter.augment_prompt(original_prompt)

    assert "--- System Context ---" in augmented_prompt
    assert "Workflow State: Coder" in augmented_prompt
    assert "Git Branch: feature-branch" in augmented_prompt
    assert "Git Commit: abc1234" in augmented_prompt
    assert "Git Status: clean" in augmented_prompt
    assert "Meta-Requirements: [\'req1\', \'req2\']" in augmented_prompt
    assert f"User Requirement: {original_prompt}" in augmented_prompt
