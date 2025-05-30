@echo off
setlocal
title ETS2LA-Lite Updater

echo.
echo ETS2LA-Lite Updater
echo -------------------
echo.

cd /d %~dp0

set "PATH=%cd%\python\Scripts;%cd%\python"

if not exist "%cd%\python" (
    echo ETS2LA-Lite is not installed, use the Installer.bat to install it!
    echo.
    goto :end
)

echo Updating App...

python -c "import time; time.sleep(3)"

python app/update.py

python -m pip install -r config/requirements.txt

echo.
echo App Updated
echo -----------
echo.

:end
endlocal
pause