import unittest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from dw6.state_manager import WorkflowManager

class TestWorkflowManagerIntegration(unittest.TestCase):

    @patch('dw6.state_manager.Governor')
    @patch('dw6.state_manager.WorkflowState')
    def test_approve_calls_governor(self, MockWorkflowState, MockGovernor):
        """Ensure that calling approve on the manager delegates to the governor."""
        # Arrange
        mock_governor_instance = MockGovernor.return_value
        manager = WorkflowManager()
        manager.governor = mock_governor_instance

        # Act
        manager.approve(next_stage='NextStage', with_tech_debt=True)

        # Assert
        mock_governor_instance.approve.assert_called_once_with(next_stage='NextStage', with_tech_debt=True)

if __name__ == '__main__':
    unittest.main()
