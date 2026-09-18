@echo off
cd /d "%~dp0backend"
call ..\venv\Scripts\activate
echo Starting backend server on http://localhost:8000 ...
echo Leave this window open. Close it or press Ctrl+C to stop the server.
uvicorn main:app --reload --port 8000
pause
