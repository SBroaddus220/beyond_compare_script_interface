#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module contains the BeyondCompareScript class, which is used to create and run Beyond Compare scripts.
"""


import logging
from pathlib import Path

# Adds package to path
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from beyond_compare_script_interface.beyond_compare_script import BeyondCompareScript

# **********
# Sets up logger
logger = logging.getLogger(__name__)

PROGRAM_LOG_FILE_PATH = Path(__file__).resolve().parent.parent / "program_log.txt"

LOGGER_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,  # Doesn't disable other loggers that might be active
    "formatters": {
        "default": {
            "format": "[%(levelname)s][%(funcName)s] | %(asctime)s | %(message)s",
        },
        "simple": {  # Used for console logging
            "format": "[%(levelname)s][%(funcName)s] | %(message)s",
        },
    },
    "handlers": {
        "logfile": {
            "class": "logging.FileHandler",  # Basic file handler
            "formatter": "default",
            "level": "INFO",
            "filename": PROGRAM_LOG_FILE_PATH.as_posix(),
            "mode": "a",
            "encoding": "utf-8",
        },
        "console_stdout": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "level": "DEBUG",
            "stream": "ext://sys.stdout",
        },
        "console_stderr": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "level": "ERROR",
            "stream": "ext://sys.stderr",
        },
    },
    "root": {  # Simple program, so root logger uses all handlers
        "level": "DEBUG",
        "handlers": [
            "logfile",
            "console_stdout",
            "console_stderr",
        ]
    }
}


# **********
# Data for Beyond Compare script
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
async def main():
    
    # Path to data directory at root of project
    data_directory = Path(__file__).resolve().parent.parent / "data"
    
    # Path to Beyond Compare executable
    BEYOND_COMPARE_PATH = Path("Fake/Path/To/BeyondCompare.exe")
    
    beyond_compare_mirror_script = BeyondCompareScript(
        executable_path = BEYOND_COMPARE_PATH,
        script_data = BEYOND_COMPARE_MIRROR_SCRIPT_DATA,
        data_directory = data_directory / "beyond_compare_mirror_script",
    )
    
    # Mirrors two directories
    source_directory = data_directory / "source"
    target_directory = data_directory / "target"
    
    # Directory to store report file and logs
    current_run_directory = beyond_compare_mirror_script.prepare_current_run_directory()
    
    # Writes new script with updated paths
    kwargs = {
        "source_directory": source_directory,
        "target_directory": target_directory,
        "report_file_path": current_run_directory / "beyond_compare_folder_report.html",
        "log_file_path": current_run_directory / "beyond_compare_log.log"
    }

    await beyond_compare_mirror_script.write_new_script(**kwargs)   
    
    # Runs script
    await beyond_compare_mirror_script.run_script()
    
    

# **********
if __name__ == "__main__":
    import logging.config
    logging.disable(logging.DEBUG)
    logging.config.dictConfig(LOGGER_CONFIG)
    main()
    










