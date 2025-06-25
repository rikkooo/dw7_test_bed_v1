import unittest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from dw6.state_manager import WorkflowManager

class TestValidatorStage(unittest.TestCase):

    @patch('dw6.state_manager.Path.is_dir', return_value=True)
    @patch('dw6.state_manager.Path.glob', return_value=[])
    def test_validator_fails_with_no_test_files(self, mock_glob, mock_is_dir):
        """Test that the Validator stage fails if no test files are found."""
        manager = WorkflowManager()
        with self.assertRaises(SystemExit) as cm:
            manager._validate_tests()
        self.assertEqual(cm.exception.code, 1)

    @patch('dw6.state_manager.subprocess.run')
    @patch('dw6.state_manager.Path.glob', return_value=['test_placeholder.py'])
    @patch('dw6.state_manager.Path.is_dir', return_value=True)
    def test_validator_succeeds_with_tests(self, mock_is_dir, mock_glob, mock_run):
        """Test that the Validator stage succeeds when tests are found and pass."""
        mock_run.side_effect = [
            MagicMock(returncode=0), # for uv pip install
            MagicMock(stdout='collected 1 items', returncode=0), # for pytest --collect-only
            MagicMock(stdout='== 1 passed in 0.01s ==', returncode=0) # for pytest run
        ]
        manager = WorkflowManager()
        result = manager._validate_tests()
        self.assertTrue(result)
        self.assertEqual(mock_run.call_count, 3)

if __name__ == '__main__':
    unittest.main()
