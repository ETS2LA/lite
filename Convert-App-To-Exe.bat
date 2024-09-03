@echo off
REM Title of the script window
title Convert Python App to EXE

REM Define the main script and the output directory
set MAIN_SCRIPT=app\main.py
set OUTPUT_DIR=dist

REM Clean previous build files
echo Cleaning previous builds...
rmdir /S /Q build >nul 2>&1
rmdir /S /Q %OUTPUT_DIR% >nul 2>&1
del /Q *.spec >nul 2>&1

REM Run PyInstaller with the required options
echo Converting %MAIN_SCRIPT% to an executable...
pyinstaller --onefile --noconsole --add-data "app\assets;assets" --add-data "app\plugins;plugins" --add-data "cache;cache" --add-data "config;config" %MAIN_SCRIPT%

REM Check if the conversion was successful
if exist %OUTPUT_DIR%\main.exe (
    echo Conversion successful! Your executable is located in the "%OUTPUT_DIR%" folder.
) else (
    echo Conversion failed! Please check the output above for errors.
)

REM Pause to allow the user to read the output
pause