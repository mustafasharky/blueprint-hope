@echo off
cd /d "%~dp0"
set "BLUEPRINT_PYTHON=py"
if exist ".venv\Scripts\python.exe" set "BLUEPRINT_PYTHON=.venv\Scripts\python.exe"
if exist "private\browser_plan.json" (
    "%BLUEPRINT_PYTHON%" blueprint_browser.py sync
) else (
    "%BLUEPRINT_PYTHON%" blueprint_browser.py capture
)
pause
