@echo off
cd /d "%~dp0"
if exist ".tools\python\python.exe" (
    ".tools\python\python.exe" run.py %*
) else if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" run.py %*
) else (
    py -3.13 run.py %*
)
if errorlevel 1 pause
