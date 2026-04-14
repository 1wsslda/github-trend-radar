@echo off
setlocal
cd /d "%~dp0"

title GitSonar - One Click Build
echo [GitSonar] Building EXE and installer...
echo.
powershell -ExecutionPolicy Bypass -NoLogo -File ".\build_setup.ps1"
set "EXIT_CODE=%ERRORLEVEL%"
echo.

if not "%EXIT_CODE%"=="0" (
  echo Build failed. See the error output above.
) else (
  echo Build complete.
  echo EXE: dist\GitSonar.exe
  echo Installer: dist\installer\GitSonarSetup.exe
)

echo.
pause
exit /b %EXIT_CODE%
