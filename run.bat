@echo off
cd /d "%~dp0"
echo Starting Amazon Geo-Rank Scraper...
poetry run python main_ui.py
if %errorlevel% neq 0 (
    echo.
    echo Application exited with error. Press any key to close.
    pause >nul
)
