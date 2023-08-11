#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module contains the BeyondCompareScript class, which is used to create and run Beyond Compare scripts.
"""

import logging
import aiofiles
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from beyond_compare_script_interface.utilities.utilities import run_command

# **********
# Sets up logger
logger = logging.getLogger(__name__)


# **********
class BeyondCompareScript:
    """Represents a Beyond Compare script. This class is able to create and run Beyond Compare scripts using subprocesses"""
    
    def __init__(self, executable_path: Path, script_data: str, data_directory: Path) -> None:
        """Instantiates a BeyondCompareScript object.

        Args:
            executable_path (Path): Path to the Beyond Compare executable.
            script_data (str): Data of script to be written according to Beyond Compare's scripting syntax.
            data_directory (Path): Directory for script and reports.

        Raises:
            EnvironmentError: If the Beyond Compare executable is not found.
        """
        self.executable_path = executable_path
        self.script_data = script_data
        self.data_directory = data_directory
        self.data_directory.mkdir(parents=True, exist_ok=True)
        
        #: The command that will be used to run the script.
        self.subprocess_command: Optional[List] = None
        
        #: The directory where the script and report files will be saved. 
        self.current_run_directory: Optional[Path] = None
        
        #: The path to the script file.
        self.script_path: Optional[Path] = None
        
        # Ensures Beyond Compare executable exists and is an executable file
        logger.debug(f"Ensuring executable exists and is an executable file.")
        if self.executable_path is None or not (self.executable_path.stat().st_mode & 0o111):
            raise EnvironmentError(f"Beyond Compare executable not found at `{self.executable_path}`.")
        
        
    def prepare_current_run_directory(self) -> Path:
        """Prepares and creates the current run directory for the script.
        The current run directory is a timestamped directory in the data directory that contains the script and report files.

        Returns:
            Path: Current run directory path.
        """
        currentDate = datetime.now()
        self.current_run_directory = self.data_directory / currentDate.strftime("%Y%m%d-%H%M%S")        
        logger.info(f"Creating current run directory at {self.current_run_directory}")
        self.current_run_directory.mkdir(parents=True, exist_ok=True)
        
        return self.current_run_directory  # return the path for use elsewhere
        
        
    async def write_new_script(self, **kwargs) -> None:
        """Writes a new script file to the current run directory using the script data and the given keyword arguments.

        Raises:
            ValueError: If the current run directory has not been set up.
        """
        
        # Checks if the current run directory has been set up.
        if not self.current_run_directory:
            raise ValueError("Current run directory not set. Set it up first.")
        
        logger.info(f"Writing new script file to {self.current_run_directory}")
        self.script_path = self.current_run_directory / "beyond_compare_script.txt"
        async with aiofiles.open(self.script_path, "w") as beyond_compare_script:
            await beyond_compare_script.write(self.script_data.format(**kwargs))
            
        # Resets current run directory to None so that it must be set up again next time.
        self.current_run_directory = None
            
            
    async def run_script(self, print_output: bool = True) -> None:
        """Runs the script using a subprocess.

        Args:
            print_output (bool, optional): Whether to print the output to the console. Defaults to True.

        Raises:
            ValueError: If the script path has not been set up.
            FileNotFoundError: If the script file is not found.
        """
        self.prepare_subprocess_command()
        logger.info(f"Running script at {self.script_path}")
        try:
            await run_command(self.subprocess_command, print_output)
        except RuntimeError as e:
            logger.error(f"Error running script at {self.script_path}: {str(e)}")
        
        
    def prepare_subprocess_command(self) -> List:
        """Prepares and returns the command that will be used to run the script.

        Raises:
            FileNotFoundError: If the script file is None or not found.

        Returns:
            List: Command represented as a list of arguments that will be used to run the script.
        """
        if self.script_path is None or not self.script_path.exists():
            raise FileNotFoundError(f"Script file not found.")
        
        logger.info(f"Preparing subprocess command for script at {self.script_path}")
        command = [
            f'{self.executable_path}',
            f'@{self.script_path}',
            "/silent"
        ]
        
        self.subprocess_command = command
        
        return self.subprocess_command
    
    
    def remove_script(self) -> None:
        """Removes the script file.

        Raises:
            FileNotFoundError: If the script file is not found.
        """
        if self.script_path and self.script_path.exists():
            logger.info(f"Removing script file at {self.script_path}")
            self.script_path.unlink()
        else:
            raise FileNotFoundError(f"Script file not found.")
        
        
# ****************
if __name__ == '__main__':
    pass
