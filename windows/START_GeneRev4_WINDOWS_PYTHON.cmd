@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title GeneRev4 Windows - GUI (Python source launcher)

rem This launcher runs the exact Windows GUI source from the GitHub repository.
rem It avoids downloading any compiled EXE or any large artifact ZIP.
set "PYTHONPATH=%~dp0..\real;%~dp0;%PYTHONPATH%"
set "APP=%~dp0GeneRev4_Windows.py"

if not exist "%APP%" (
  echo ERROR: GeneRev4_Windows.py is missing.
  echo In GitHub Desktop: GeneRev4-Web - Fetch origin - Pull origin.
  goto :error
)
if not exist "%~dp0..\real\bridge.py" (
  echo ERROR: real\bridge.py is missing. Clone the full repository.
  goto :error
)

py -3 -c "import tkinter; import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if not errorlevel 1 (
  echo Starting GeneRev4 Windows application with Python...
  py -3 "%APP%"
  goto :done
)
python -c "import tkinter; import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if not errorlevel 1 (
  echo Starting GeneRev4 Windows application with Python...
  python "%APP%"
  goto :done
)

echo ERROR: Python 3.10+ with tkinter not found.
echo Please install Python from https://www.python.org/downloads/windows/
echo Open a new terminal and check: py -3 --version
goto :error

:done
if errorlevel 1 goto :error
exit /b 0

:error
echo.
echo The GeneRev4 Windows GUI did not start.
echo This launcher NEVER starts hardware controls automatically.
pause
exit /b 1
