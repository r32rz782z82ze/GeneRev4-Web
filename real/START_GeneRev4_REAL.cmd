@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title GeneRev4 REAL - local web TCP bridge
echo.
echo ========================================================
echo GeneRev4 REAL - Nico STM32 / ESP8266 - Windows
echo ========================================================
echo.
echo Open on THIS laptop: http://127.0.0.1:8787/
echo Not the public GitHub Pages website!
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
echo WARNING: Sending a TCP command is NOT proof of safe shutdown.
echo Independent overtemperature cutoff and physical emergency stop required!
echo Loss of TCP does NOT guarantee heater shutdown.
set "ACK="
set /p "ACK=Type FELUGYELEM to acknowledge: "
if /I not "%ACK%"=="FELUGYELEM" (
  echo Cancelled. Control was NOT enabled.
  pause
  exit /b 1
)
set "MODE=--enable-control"
:run
where py >nul 2>&1
if not errorlevel 1 (
  echo.
  echo Open: http://127.0.0.1:8787/
  py -3 "%~dp0bridge.py" %MODE%
  goto :done
)
where python >nul 2>&1
if not errorlevel 1 (
  echo.
  echo Open: http://127.0.0.1:8787/
  python "%~dp0bridge.py" %MODE%
  goto :done
)
echo ERROR: Python 3.10+ missing. Get it from python.org.
:done
echo.
echo The bridge is closed. CHECK physical hardware state!
pause
