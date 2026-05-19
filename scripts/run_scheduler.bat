@echo off
cd C:\ai-agents\ai-job-search-pipeline
call C:\ai-agents\venv\Scripts\activate
start "AI Job Search - Live Log" powershell.exe -NoExit -ExecutionPolicy Bypass -File "C:\ai-agents\ai-job-search-pipeline\scripts\tail_log.ps1"
python scheduler.py
