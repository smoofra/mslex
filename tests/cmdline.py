#!/usr/bin/env python

# This is a helper script for creating test data for mslex.
#
# If python is a modern build from python.org, then it will be linked
# against UCRT, so sys.argv can be used to record how UCRT interprets the
# command line.
#
# CommandLineToArgvW() should match what msvcrt.dll does.
#
# The output of GetCommandLineW() is recorded here so we know exactly what
# cmd.exe did to the command line

import sys
import json
import ctypes
from ctypes import windll, POINTER, c_int
from ctypes.wintypes import LPCWSTR, HLOCAL, LPWSTR

kernel32 = windll.kernel32
shell32 = windll.shell32

CommandLineToArgvW = shell32.CommandLineToArgvW
CommandLineToArgvW.argtypes = [LPCWSTR, POINTER(c_int)]
CommandLineToArgvW.restype = POINTER(LPWSTR)

LocalFree = kernel32.LocalFree
LocalFree.argtypes = [HLOCAL]
LocalFree.restype = HLOCAL

GetCommandLineW = kernel32.GetCommandLineW
GetCommandLineW.restype = ctypes.c_wchar_p


def main():
    cmdline = GetCommandLineW()

    argc = c_int()
    argv = CommandLineToArgvW(cmdline, ctypes.byref(argc))
    args = [argv[i] for i in range(argc.value)]
    LocalFree(argv)

    j = {
        "GetCommandLineW": cmdline,
        "CommandLineToArgvW": args,
        "sys.argv": sys.argv,
    }
    json.dump(j, sys.stdout, indent=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
