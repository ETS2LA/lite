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

%cd%\python\python.exe -c "import subprocess; import time; time.sleep(0.5); subprocess.Popen(['python', 'app/update.py'])"

timeout /t 15 /nobreak

%cd%\python\python.exe -m pip install -r config/requirements.txt -q

echo.
echo App Updated
echo -----------
echo.

:end
endlocal
pause