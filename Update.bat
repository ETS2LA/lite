@echo off
setlocal
title ETS2LA-Lite Updater

echo.
echo ETS2LA-Lite Updater
echo -------------------
echo.

set "PATH=%cd%\python\Scripts;%cd%\python"

if not exist "%cd%\python" (
    echo ETS2LA-Lite is not installed, use the Installer.bat to install it!
    echo.
    goto :end
)

echo INFORMATION: Updating not implemented yet.

echo Installing requirements...
pip install -r config/requirements.txt -q
echo Done.

echo.
echo App Updated
echo -----------
echo.

:end
endlocal
pause