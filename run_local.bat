@echo off
setlocal enabledelayedexpansion
title JESA Pipe Support Selector — Local Server

echo ============================================================
echo  JESA Pipe Support Selector — Local Development Server
echo ============================================================
echo.

:: ── Locate this script's directory (project root) ────────────────────────────
cd /d "%~dp0"

:: ── Pick Python interpreter ───────────────────────────────────────────────────
:: Prefer .venv if it exists, then fall back to system Python.

set PYTHON=
set VENV_ACTIVATED=0

if exist ".venv\Scripts\activate.bat" (
    echo [1/4] Found .venv — activating virtual environment...
    call ".venv\Scripts\activate.bat"
    set PYTHON=python
    set VENV_ACTIVATED=1
) else (
    echo [1/4] No .venv found — using system Python installation.
    where python >nul 2>&1
    if !errorlevel! == 0 (
        set PYTHON=python
    ) else (
        where python3 >nul 2>&1
        if !errorlevel! == 0 (
            set PYTHON=python3
        ) else (
            echo.
            echo  ERROR: Python was not found on PATH.
            echo  Install Python from https://www.python.org/downloads/
            echo  and make sure "Add Python to PATH" is checked during install.
            echo.
            pause
            exit /b 1
        )
    )
)

%PYTHON% --version
echo.

:: ── Check / install dependencies ─────────────────────────────────────────────
echo [2/4] Checking dependencies...

%PYTHON% -c "import flask, fitz, dotenv" >nul 2>&1
if !errorlevel! neq 0 (
    echo  Some packages are missing. Installing from requirements.txt...
    echo.
    %PYTHON% -m pip install -r requirements.txt
    if !errorlevel! neq 0 (
        echo.
        echo  ERROR: pip install failed.
        echo  Try running: %PYTHON% -m pip install -r requirements.txt
        echo  in this folder, then re-run this launcher.
        echo.
        pause
        exit /b 1
    )
    echo.
    echo  Dependencies installed successfully.
) else (
    echo  All required packages found.
)
echo.

:: ── Set environment ───────────────────────────────────────────────────────────
echo [3/4] Setting environment...
set FLASK_ENV=development
set FLASK_DEBUG=1
set PORT=5000
echo  FLASK_ENV=development  ^|  PORT=%PORT%
echo.

:: ── Launch app and open browser ───────────────────────────────────────────────
echo [4/4] Starting Flask server at http://127.0.0.1:%PORT%
echo       Press Ctrl+C to stop the server.
echo ============================================================
echo.

:: Open the browser after a short delay (1.5 s) so Flask has time to bind.
start "" /b cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:%PORT%"

%PYTHON% app.py

:: ── Server exited ─────────────────────────────────────────────────────────────
echo.
echo ============================================================
echo  Server has stopped.
echo ============================================================
pause
