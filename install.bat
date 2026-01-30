@echo off
setlocal enabledelayedexpansion

echo ========================================
echo  Amazon Geo-Rank Scraper - Installer
echo ========================================
echo.

:: Check for Python
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.11+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%a in ('python --version 2^>^&1') do set PYVER=%%a
echo Found Python %PYVER%

:: Check Python version is 3.11+
for /f "tokens=1,2 delims=." %%a in ("%PYVER%") do (
    set MAJOR=%%a
    set MINOR=%%b
)
if %MAJOR% lss 3 (
    echo ERROR: Python 3.11+ is required. You have Python %PYVER%
    pause
    exit /b 1
)
if %MAJOR% equ 3 if %MINOR% lss 11 (
    echo ERROR: Python 3.11+ is required. You have Python %PYVER%
    pause
    exit /b 1
)
echo Python version OK.
echo.

:: Check for Poetry
echo [2/5] Checking Poetry installation...
poetry --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Poetry not found. Installing Poetry...
    echo.
    curl -sSL https://install.python-poetry.org | python -
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install Poetry.
        echo Please install manually: https://python-poetry.org/docs/#installation
        pause
        exit /b 1
    )
    echo.
    echo Poetry installed. You may need to restart your terminal.
    echo Add Poetry to PATH: %%APPDATA%%\Python\Scripts
    echo.
) else (
    for /f "tokens=*" %%a in ('poetry --version 2^>^&1') do echo Found %%a
)
echo.

:: Install Python dependencies
echo [3/5] Installing Python dependencies...
echo This may take a few minutes...
echo.
poetry install
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies.
    echo Try running: poetry install --no-cache
    pause
    exit /b 1
)
echo Dependencies installed.
echo.

:: Install Playwright browsers
echo [4/5] Installing Playwright browsers...
echo This will download Chromium browser (~150MB)...
echo.
poetry run playwright install chromium
if %errorlevel% neq 0 (
    echo ERROR: Failed to install Playwright browsers.
    echo Try running: poetry run playwright install
    pause
    exit /b 1
)
echo Playwright browsers installed.
echo.

:: Create necessary directories
echo [5/5] Creating directories...
if not exist "results" mkdir results
if not exist "user_data" mkdir user_data
echo Directories created.
echo.

echo ========================================
echo  Installation Complete!
echo ========================================
echo.
echo To run the application:
echo   poetry run python main_ui.py
echo.
echo Or double-click: run.bat
echo.
pause
