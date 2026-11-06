@echo off
setlocal
title Japanese Learning App - Installer
set "REPO=https://github.com/mxxs109-ops/japanese-learning-app/archive/refs/heads/main.zip"

for /f "usebackq delims=" %%d in (`powershell -NoProfile -Command "[Environment]::GetFolderPath('Desktop')"`) do set "DESK=%%d"
if not defined DESK set "DESK=%USERPROFILE%\Desktop"
set "DEST=%DESK%\japanese learning app"
set "ZIP=%TEMP%\jla_download.zip"
set "TMPX=%TEMP%\jla_extract"

echo.
echo   Downloading...
"%SystemRoot%\System32\curl.exe" -sL -o "%ZIP%" "%REPO%"
if errorlevel 1 goto fail

if exist "%TMPX%" rmdir /s /q "%TMPX%"
mkdir "%TMPX%"
"%SystemRoot%\System32\tar.exe" -xf "%ZIP%" -C "%TMPX%"
if errorlevel 1 goto fail
if not exist "%TMPX%\japanese-learning-app-main\index.html" goto fail

if not exist "%DEST%" mkdir "%DEST%"
copy /y "%TMPX%\japanese-learning-app-main\index.html"   "%DEST%\" >nul
copy /y "%TMPX%\japanese-learning-app-main\questions.js" "%DEST%\" >nul
copy /y "%TMPX%\japanese-learning-app-main\srs.js"       "%DEST%\" >nul
rmdir /s /q "%TMPX%"
del /q "%ZIP%"

echo   Done:  %DEST%
start "" "%DEST%\index.html"
echo.
echo   Closing in 3...
ping -n 2 127.0.0.1 >nul
echo   2...
ping -n 2 127.0.0.1 >nul
echo   1...
ping -n 2 127.0.0.1 >nul
exit

:fail
echo.
echo   [FAIL] Download failed. Check your internet and try again.
pause
exit /b 1
