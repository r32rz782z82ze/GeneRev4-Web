@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title GeneRev4 REAL - local web TCP bridge
echo.
echo ========================================================
echo GeneRev4 REAL - Nico STM32 / ESP8266 - Windows
echo ========================================================
echo.

rem Check for a REAL Python interpreter; where python can find only the
rem Windows Microsoft Store execution alias and falsely report success.
set "PYTHON="
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if not errorlevel 1 set "PYTHON=py -3"
if not defined PYTHON (
  python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
  if not errorlevel 1 set "PYTHON=python"
)
if not defined PYTHON goto :no_python

echo Python interpreter OK.
echo Local page: http://127.0.0.1:8787/
echo This is NOT the public GitHub Pages website.
echo.
echo 1 - MONITOR ONLY: actual readings, NO hardware commands
echo 2 - SUPERVISED MANUAL CONTROL: START, STOP, COOL, target
echo.
choice /C 12 /N /M "Choose [1/2]: "
set "MODE="
if errorlevel 2 goto :confirm
goto :run
:confirm
echo.
echo WARNING: TCP commands are NOT proof of safe hardware shutdown.
echo Independent overtemperature cutoff and physical emergency stop required!
echo Loss of TCP does NOT guarantee heater shutdown.
set "ACK="
set /p "ACK=Type FELUGYELEM to acknowledge: "
if /I not "%ACK%"=="FELUGYELEM" (
  echo Cancelled. Hardware control was NOT enabled.
  pause
  exit /b 1
)
set "MODE=--enable-control"
:run
echo.
echo Server starting at http://127.0.0.1:8787/
echo Keep this window OPEN while using GeneRev4 REAL.
%PYTHON% "%~dp0bridge.py" %MODE%
goto :done
:no_python
echo ERROR: Python 3.10 or newer was NOT found.
echo Windows may be redirecting the python command to Microsoft Store.
echo Install Python 3.12 from https://www.python.org/downloads/windows/
echo Select "Add python.exe to PATH" in the Python installer.
echo Then restart Command Prompt and verify: py -3 --version
echo.
:done
echo The local bridge has STOPPED or did NOT start.
echo CHECK physical roaster state independently.
pause
