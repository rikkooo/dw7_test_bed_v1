import unittest
from unittest.mock import patch, mock_open
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from dw6.state_manager import WorkflowManager

class TestStateManager(unittest.TestCase):

    @patch('dw6.state_manager.WorkflowState')
    @patch('dw6.state_manager.git_handler.GitManager')
    @patch('builtins.open', new_callable=mock_open)
    def test_post_transition_actions_generates_coder_deliverable(self, mock_file_open, MockGitManager, MockWorkflowState):
        """Test that post-transition actions generate a Coder deliverable."""
        # Arrange
        mock_state = MockWorkflowState.return_value
        mock_state.get.side_effect = ['Coder', 'Coder', 'abcde123', 'abcde123']

        mock_git = MockGitManager.return_value
        mock_git.get_current_commit_sha.return_value = 'fghij456'
        mock_git.get_changes.return_value = (['file1.py'], 'diff --git a/file1.py b/file1.py')

        manager = WorkflowManager()
        manager.state = mock_state

        # Act
        manager._run_post_transition_actions('Coder')

        # Assert
        deliverable_path = Path("deliverables/coding/coder_deliverable.md")
        mock_file_open.assert_called_once_with(deliverable_path, 'w')
        handle = mock_file_open()
        written_content = "".join(call.args[0] for call in handle.write.call_args_list)
        self.assertIn("# Coder Stage Deliverable", written_content)

if __name__ == '__main__':
    unittest.main()
