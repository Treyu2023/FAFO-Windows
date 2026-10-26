@echo off
cd /d "%~dp0"
start "FAFO Toolbox" /min py -3 shell_server.py
timeout /t 1 /nobreak >nul
start "" "http://127.0.0.1:18770/"
