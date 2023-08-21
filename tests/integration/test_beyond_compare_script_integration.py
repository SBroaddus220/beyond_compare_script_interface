#!/usr/bin/env python
# -*- coding: utf-8 -*-


""" 
Test cases for the beyond compare script class.
"""

import os
import asyncio
import tempfile
import shutil
import filecmp
import logging
from pathlib import Path

import unittest

from beyond_compare_script_interface.beyond_compare_script import BeyondCompareScript


# **********
# Sets up logger
logger = logging.getLogger(__name__)

# **********
# Beyond Compare script data
BEYOND_COMPARE_MIRROR_SCRIPT_DATA = """\
criteria attrib:ashr timestamp:2sec size
load "{source_directory}" "{target_directory}"
expand all
folder-report layout:side-by-side &
options:display-mismatches,include-file-links &
title:test &
output-to:"{report_file_path}" &
output-options:html-color
log verbose "{log_file_path}"
sync create-empty mirror:left->right\
"""

# **********
# Gets environment variable for executable path
BEYOND_COMPARE_PATH = os.environ.get("BEYOND_COMPARE_PATH")
if BEYOND_COMPARE_PATH is not None:
    BEYOND_COMPARE_PATH = Path(BEYOND_COMPARE_PATH) 

# **********
def are_dir_trees_equal(dir1: Path, dir2: Path) -> bool:
    """
    Retrieved from `https://stackoverflow.com/questions/4187564/recursively-compare-two-directories-to-ensure-they-have-the-same-files-and-subdi`.
    Originally written by user `Mateusz Kobos`
    Compare two directories recursively. Files in each directory are
    assumed to be equal if their names and contents are equal.

    Args:
        dir1 (Path): First directory path
        dir2 (Path): Second directory path

    Returns:
        bool: Whether the directory trees are equal.
    """
    logger.info(f"Comparing directory trees: {dir1} and {dir2}")
    dirs_cmp = filecmp.dircmp(dir1, dir2)
    if len(dirs_cmp.left_only)>0 or len(dirs_cmp.right_only)>0 or \
        len(dirs_cmp.funny_files)>0:
        return False
    (_, mismatch, errors) =  filecmp.cmpfiles(
        dir1, dir2, dirs_cmp.common_files, shallow=False)
    if len(mismatch)>0 or len(errors)>0:
        return False
    for common_dir in dirs_cmp.common_dirs:
        new_dir1 = os.path.join(dir1, common_dir)
        new_dir2 = os.path.join(dir2, common_dir)
        if not are_dir_trees_equal(new_dir1, new_dir2):
            return False
    return True


# ****************
@unittest.skipIf(BEYOND_COMPARE_PATH is None, "Beyond Compare executable environment variable not set.")
class TestBeyondCompareScriptIntegration(unittest.TestCase):
    
    # ****************
    def setUp(self):
        
        self.test_dir = Path(tempfile.mkdtemp())
        self.source_directory = self.test_dir / "source"
        self.target_directory = self.test_dir / "target"
        
        # Mirror script setup
        mirror_script_data_directory = self.test_dir / "mirror_script"
        mirror_script_data_directory.mkdir(parents=True, exist_ok=True)
        self.mirror_script = BeyondCompareScript(
            executable_path = Path(BEYOND_COMPARE_PATH),
            script_data = BEYOND_COMPARE_MIRROR_SCRIPT_DATA, 
            data_directory = mirror_script_data_directory
        )
        self.mirror_script_run_directory = self.mirror_script.prepare_current_run_directory()
        
        self.mirror_script_kwargs = {
            "source_directory": self.source_directory,
            "target_directory": self.target_directory,
            "report_file_path": self.mirror_script_run_directory / "beyond_compare_folder_report.html",
            "log_file_path": self.mirror_script_run_directory / "beyond_compare_log.log"
        }
        
        # Ensures directories exist and are empty
        for directory in [self.source_directory, self.target_directory]:
            shutil.rmtree(directory) if directory.exists() else None
            directory.mkdir(parents=True, exist_ok=True)
        

    # *****
    # Mirror script tests
    def test_mirror_script_empty_source_empty_target(self):
        # Ensures directories are empty
        self.assertTrue(not any(self.source_directory.iterdir()))
        self.assertTrue(not any(self.target_directory.iterdir()))
        
        # Copies file to target directory
        asyncio.run(self.mirror_script.write_new_script(**self.mirror_script_kwargs))
        
        # Runs the script
        asyncio.run(self.mirror_script.run_script())
        
        # Ensures directory contents are the same and both empty
        self.assertTrue(are_dir_trees_equal(self.source_directory, self.target_directory))
        self.assertTrue(not any(self.source_directory.iterdir()))
        self.assertTrue(not any(self.target_directory.iterdir()))
        
    
    def test_mirror_script_empty_source_nonempty_target(self):
        # Ensures directories are empty
        self.assertTrue(not any(self.source_directory.iterdir()))
        self.assertTrue(not any(self.target_directory.iterdir()))
        
        # Creates file in target directory
        with tempfile.NamedTemporaryFile(dir=self.target_directory, delete=False) as temp:
            temp.write(b'Some data')  # Write bytes to the file
        
        # Copies file to target directory
        asyncio.run(self.mirror_script.write_new_script(**self.mirror_script_kwargs))
        
        # Runs the script
        asyncio.run(self.mirror_script.run_script())
        
        # Ensures directory contents are the same
        self.assertTrue(are_dir_trees_equal(self.source_directory, self.target_directory))
        self.assertTrue(not any(self.source_directory.iterdir()))
    
    
    def test_mirror_script_nonempty_source_empty_target(self):
        # Ensures directories are empty
        self.assertTrue(not any(self.source_directory.iterdir()))
        self.assertTrue(not any(self.target_directory.iterdir()))
        
        # Creates file in source directory
        with tempfile.NamedTemporaryFile(dir=self.source_directory, delete=False) as temp:
            temp.write(b'Some data')  # Write bytes to the file
        
        # Copies file to target directory
        asyncio.run(self.mirror_script.write_new_script(**self.mirror_script_kwargs))
        
        # Runs the script
        asyncio.run(self.mirror_script.run_script())
        
        # Ensures directory contents are the same
        self.assertTrue(are_dir_trees_equal(self.source_directory, self.target_directory))
        
           
    def test_mirror_script_nonempty_source_nonempty_target(self):
        # Ensures directories are empty
        self.assertTrue(not any(self.source_directory.iterdir()))
        self.assertTrue(not any(self.target_directory.iterdir()))
        
        # Creates file in source directory
        with tempfile.NamedTemporaryFile(dir=self.source_directory, delete=False) as temp:
            temp.write(b'Some data')  # Write bytes to the file
            
        with tempfile.NamedTemporaryFile(dir=self.target_directory, delete=False) as temp:
            temp.write(b'Some data')  # Write bytes to the file
        
        # Copies file to target directory
        asyncio.run(self.mirror_script.write_new_script(**self.mirror_script_kwargs))
        
        # Runs the script
        asyncio.run(self.mirror_script.run_script())
        
        # Ensures directory contents are the same
        self.assertTrue(are_dir_trees_equal(self.source_directory, self.target_directory))


# ****************
if __name__ == '__main__':
    unittest.main()
