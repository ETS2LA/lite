@echo off
setlocal
title ETS2LA-Lite Console

echo.
echo ETS2LA-Lite
echo -----------
echo.

set "PATH=%cd%\python\Scripts;%cd%\python;%cd%\git\bin"

set "missing=0"
if not exist "%cd%\python" (
    set "missing=1"
)
if not exist "%cd%\git" (
    set "missing=1"
)
if %missing%==1 (
    echo ETS2LA-Lite is not installed, use the Installer.bat to install it!
    echo.
    goto :end
)

python app/main.py

:end
endlocal
pause