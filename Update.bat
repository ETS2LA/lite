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

echo Updating App...

%cd%\python\python.exe -c "import time; time.sleep(3)"

%cd%\python\python.exe app/update.py

%cd%\python\python.exe -m pip install -r config/requirements.txt

echo.
echo App Updated
echo -----------
echo.

:end
endlocal
pause