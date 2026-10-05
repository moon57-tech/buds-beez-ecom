@echo off
echo Starting Buds & Beez E-commerce Site...
cd /d "%~dp0"
call venv\Scripts\activate.bat
python server.py
pause
