@echo off
setlocal
title ETS2LA-Lite Updater

echo.
echo ETS2LA-Lite Updater
echo -------------------
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

echo Stashing changes...
git stash

echo Pulling changes...
git pull

echo Installing requirements...
pip install -r config/requirements.txt -q

echo.
echo App Updated
echo -----------
echo.

:end
endlocal
pause