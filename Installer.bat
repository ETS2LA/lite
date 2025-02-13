@echo off
setlocal


title ETS2LA-Lite Installer

echo.
echo ETS2LA-Lite Installer
echo ---------------------
echo.


if exist "%cd%\python" (
    if exist "%cd%\git" (
        echo ETS2LA-Lite is already installed, press enter to reinstall!
        echo.
        pause
        echo.
    )
)


set "GitUrl=https://cyfuture.dl.sourceforge.net/project/git-for-windows.mirror/v2.47.1.windows.2/PortableGit-2.47.1.2-64-bit.7z.exe?viasf=1"
set "GitSavePath=%cd%\PortableGit-2.47.1.2-64-bit.7z.exe"

echo Downloading Git...
where curl >nul 2>&1
if %errorlevel% equ 0 (
    curl -s -o "%GitSavePath%" "%GitUrl%" >nul 2>&1
) else (
    powershell -Command "$wc = New-Object System.Net.WebClient; $wc.DownloadFile('%GitUrl%', '%GitSavePath%')"
)

set "GitZipPath=%GitSavePath%"
set "GitExtractPath=%cd%\git"

echo Extracting Git...

if exist "%GitExtractPath%" (
    rmdir /s /q "%GitExtractPath%"
)

%GitSavePath%  -y -o"%GitExtractPath%" >nul 2>&1


set "PythonUrl=https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"
set "PythonSavePath=%cd%\Python-3.11.9.zip"

echo Downloading Python...
where curl >nul 2>&1
if %errorlevel% equ 0 (
    curl -s -o "%PythonSavePath%" "%PythonUrl%" >nul 2>&1
) else (
    powershell -Command "$wc = New-Object System.Net.WebClient; $wc.DownloadFile('%PythonUrl%', '%PythonSavePath%')"
)


set "PythonZipPath=%PythonSavePath%"
set "PythonExtractPath=%cd%\python"

echo Extracting Python...

if exist "%PythonExtractPath%" (
    rmdir /s /q "%PythonExtractPath%"
)

mkdir "%PythonExtractPath%" >nul 2>&1
powershell -Command "Expand-Archive -Path '%PythonZipPath%' -DestinationPath '%PythonExtractPath%' -Force"


echo Getting pip...

set "PipUrl=https://bootstrap.pypa.io/get-pip.py"
set "PipSavePath=%PythonExtractPath%\get-pip.py"

where curl >nul 2>&1
if %errorlevel% equ 0 (
    curl -s -o "%PipSavePath%" "%PipUrl%" >nul 2>&1
) else (
    powershell -Command "$wc = New-Object System.Net.WebClient; $wc.DownloadFile('%PipUrl%', '%PipSavePath%')"
)

"%PythonExtractPath%\python.exe" "%PipSavePath%" >nul 2>&1


echo Editing installations...

set "PthFilePath=%PythonExtractPath%\python311._pth"

if exist "%PthFilePath%" (
    echo Lib\site-packages >> "%PthFilePath%"
    powershell -Command "(gc '%PthFilePath%') -replace '#import site','import site' | Out-File -encoding ASCII '%PthFilePath%'"
) else (
    echo ERROR: File not found: %PthFilePath%
    pause
)

if exist "%GitSavePath%" (
    del "%GitSavePath%"
)

if exist "%PythonSavePath%" (
    del "%PythonSavePath%"
)


echo Done.
echo.


echo Git Version:
%GitExtractPath%\bin\git.exe --version
echo.

echo Python Version:
%PythonExtractPath%\python.exe  --version
echo.

echo Pip Version:
%PythonExtractPath%\python.exe -m pip --version
echo.

echo Pip Packages:
%PythonExtractPath%\python.exe -m pip list


echo.
echo App Installed
echo -------------
echo.

endlocal
pause