@echo off
setlocal
title ETS2LA-Lite Console

echo.
echo ETS2LA-Lite
echo -----------
echo.

set "PATH=%cd%\python\Scripts;%cd%\python"

if not exist "%cd%\python" (
    echo ETS2LA-Lite is not installed, use the Installer.bat to install it!
    echo.
    goto :end
)

python app/main.py

:end
endlocal
pause