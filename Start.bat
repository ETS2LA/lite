@echo off
cd %~dp0
if not exist venv (
    echo Creating venv...
    python -m venv venv
)
call venv\Scripts\activate
python main.py
pause