@echo off
cd %~dp0

if exist venv (\python venv\Scripts\activate.bat)
else (\python -m venv venv)
\python venv\Scripts\activate.bat
cd %~dp0
python main.py
pause