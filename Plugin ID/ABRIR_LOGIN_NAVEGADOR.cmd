@echo off
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
  start "" /min py -3 "%~dp0auth_server_plugin.py"
) else (
  start "" /min python "%~dp0auth_server_plugin.py"
)
exit /b 0
