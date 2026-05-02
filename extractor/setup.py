# =============================================================================
#     Author: J Glass
#     Date:   Aug 8 2018
#
#     File:  setup.py
#     Description: This is the cx_Freeze setup file for creating a Win32 app
# =============================================================================

import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
include_files = ['nhl_94.ttf']
build_exe_options = {"packages": ["os"], "excludes": [], "include_files": include_files}
# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

exe = Executable(
    # what to build
    script="Stat_Extractor.py",  # the name of your main python script goes here
    targetName="Stat Extractor.exe",  # this is the name of the executable file
    base=base
    # icon="icon.ico"
)

setup(
    # the actual setup & the definition of other misc. info
    name="NHL94 Offline Stat Extractor",  # program name
    version="0.1",
    author="chaos",
    options={"build_exe": build_exe_options},
    executables=[exe]
)
