@echo off
cd /d "%~dp0"
start "Startup List" /min py -3 server.py
timeout /t 1 /nobreak >nul
start "" "http://127.0.0.1:18774/"
