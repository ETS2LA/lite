@echo off
rem Compile the main application using Nuitka
nuitka ^
--standalone ^
--plugin-enable=pylint-warnings ^
--plugin-enable=multiprocessing ^
--include-data-dir=app=app ^
--include-data-dir=config=config ^
--include-data-dir=cache=cache ^
--output-dir=dist ^
--follow-imports ^
app/main.py
pause
