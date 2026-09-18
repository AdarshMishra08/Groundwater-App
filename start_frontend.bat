@echo off
cd /d "%~dp0frontend"
call ..\venv\Scripts\activate
echo Starting dashboard... your browser should open automatically.
echo Leave this window open. Close it or press Ctrl+C to stop the dashboard.
streamlit run app.py
pause
