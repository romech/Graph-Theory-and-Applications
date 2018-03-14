import sys
from cx_Freeze import setup, Executable
from os import environ
# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {"packages": ["os","pyx"], "include_files": ["tcl86t.dll", "tk86t.dll"]}
environ['TCL_LIBRARY'] = r'C:\Users\1\AppData\Local\Programs\Python\Python35\tcl\tcl8.6'
environ['TK_LIBRARY'] = r'C:\Users\1\AppData\Local\Programs\Python\Python35\tcl\tk8.6'
# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(  name = "OSM Processing Application",
        version = "0.1",
        description = "OSM Processing App. It may look like frozen, but it is not.",
        options = {"build_exe": build_exe_options},
        executables = [Executable("OSM_processing.py", base=base)])
