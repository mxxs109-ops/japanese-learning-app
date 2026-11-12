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
copy /y "%TMPX%\japanese-learning-app-main\icon.ico"     "%DEST%\" >nul
copy /y "%TMPX%\japanese-learning-app-main\icon.png"     "%DEST%\" >nul
if exist "%TMPX%\japanese-learning-app-main\images" xcopy /e /i /y /q "%TMPX%\japanese-learning-app-main\images" "%DEST%\images" >nul
if exist "%TMPX%\japanese-learning-app-main\audio" xcopy /e /i /y /q "%TMPX%\japanese-learning-app-main\audio" "%DEST%\audio" >nul
rmdir /s /q "%TMPX%"
del /q "%ZIP%"

rem folder icon
if exist "%DEST%\desktop.ini" attrib -h -s -r "%DEST%\desktop.ini"
> "%DEST%\desktop.ini" echo [.ShellClassInfo]
>> "%DEST%\desktop.ini" echo IconResource=icon.ico,0
attrib +h +s "%DEST%\desktop.ini"
attrib +r "%DEST%"

rem desktop shortcut that opens the app
powershell -NoProfile -Command "$n=[string][char]0x65E5+[char]0x672C+[char]0x8A9E+' Daily.lnk'; $s=(New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $env:DESK $n)); $s.TargetPath=(Join-Path $env:DEST 'index.html'); $s.WorkingDirectory=$env:DEST; $s.IconLocation=(Join-Path $env:DEST 'icon.ico')+',0'; $s.Save()"
ie4uinit.exe -show >nul 2>&1

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
