@echo off
cd C:\ai-agents\ai-job-search-pipeline
call C:\ai-agents\venv\Scripts\activate
start powershell.exe -NoExit -Command "aiwork; webui"
timeout /t 5 /nobreak >nul
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --new-tab "http://localhost:5000"
