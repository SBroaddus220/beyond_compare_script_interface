#!/usr/bin/env python
# -*- coding: utf-8 -*-


""" 
Test cases for the beyond compare script class.
"""

import shutil
import logging
import asyncio
import tempfile
from pathlib import Path

import unittest
from unittest import mock
from unittest.mock import patch, AsyncMock, MagicMock, PropertyMock

from beyond_compare_script_interface.beyond_compare_script import BeyondCompareScript
from simple_async_command_manager.commands.command_bases import SubprocessCommand


# ****************
class TestBeyondCompareScript(unittest.TestCase):
    
    # ****************
    def setUp(self):
        
        # Configure logging
        self.logger = logging.getLogger(__name__)
        
        # Mocks executable path
        self.EXECUTABLE_PATH = MagicMock(spec=Path)
        type(self.EXECUTABLE_PATH).stat = PropertyMock(return_value=MagicMock(st_mode=0o700))
        
        self.test_dir = Path(tempfile.mkdtemp())
        self.script = BeyondCompareScript(
            executable_path = self.EXECUTABLE_PATH,
            script_data = "Test script", 
            data_directory = self.test_dir,
        )
        self.source_directory = self.test_dir / "source"
        self.target_directory = self.test_dir / "target"
        
        # Prepares the current run directory for the script
        self.current_run_directory = self.script.prepare_current_run_directory()
        
        # Ensures directories exist and are empty
        for directory in [self.source_directory, self.target_directory]:
            shutil.rmtree(directory) if directory.exists() else None
            directory.mkdir(parents=True, exist_ok=True)
                

    def tearDown(self):
        # Delete the temporary directory after the test
        shutil.rmtree(self.test_dir)
        
        
    # ****************
    # Write new script tests
    def test_write_new_script_correct_data(self):
        asyncio.run(self.script.write_new_script())
        self.assertIsNotNone(self.script.script_path)

        with open(self.script.script_path, "r") as f:
            content = f.read()

        expected_content = self.script.script_data.format()

        self.assertEqual(content, expected_content)


    # ****************
    # Prepare current run directory tests
    def test_prepare_current_run_directory(self):
        current_run_directory = self.script.prepare_current_run_directory()
        self.assertTrue(current_run_directory.is_dir())
        self.assertIsNotNone(self.script.current_run_directory)
    

    # ****************
    # Run script / subprocess tests
    @patch.object(SubprocessCommand, 'run', new_callable=AsyncMock)  # Mock the SubprocessCommand.run method
    def test_run_script(self, mock_run):
        self.script.script_path = self.test_dir / "beyond_compare_script.txt"
        self.script.script_path.touch()  # Create a temporary file at script_path
        self.script.prepare_subprocess_command()
        asyncio.run(self.script.run_script())
        # Verify the run method was called
        mock_run.assert_called_once()


    def test_run_script_without_writing(self):
        with self.assertRaises(FileNotFoundError):
            asyncio.run(self.script.run_script())


    def test_prepare_subprocess_command(self):
        asyncio.run(self.script.write_new_script())
        command = self.script.prepare_subprocess_command()
        self.assertIsInstance(command, SubprocessCommand)
        self.assertEqual(command.command, [f'{self.script.executable_path}', f'@{self.script.script_path}', "/silent"])


    def test_run_method_prepares_subprocess(self):
        # Arrange
        mock_subprocess_command = mock.Mock()
        mock_subprocess_command.run = AsyncMock()

        # Manually sets the attribute to the required value to simulate prepare sync subprocess call
        def side_effect():
            self.script.subprocess_command = mock_subprocess_command
            return mock_subprocess_command

        with mock.patch('pathlib.Path.exists', return_value=True), \
            mock.patch.object(BeyondCompareScript, 'prepare_subprocess_command', side_effect=side_effect) as mock_prepare_subprocess_command:

            # Act
            asyncio.run(self.script.run_script())

            # Assert
            mock_prepare_subprocess_command.assert_called_once()
            mock_subprocess_command.run.assert_called_once()


    # ****************
    # Remove script tests
    def test_remove_script(self):
        self.script.script_path = self.test_dir / "beyond_compare_script.txt"
        self.script.script_path.touch()  # Create a temporary file at script_path
        self.script.remove_script()
        # Verify the file was removed
        self.assertFalse(self.script.script_path.exists())
        
        
    def test_run_script_after_removing(self):
        asyncio.run(self.script.write_new_script())
        self.script.remove_script()
        with self.assertRaises(FileNotFoundError):
            asyncio.run(self.script.run_script())
        
        
# ****************
if __name__ == '__main__':
    unittest.main()
