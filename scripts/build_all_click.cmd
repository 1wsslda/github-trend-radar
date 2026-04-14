@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "ROOT_DIR=%%~fI"
cd /d "%ROOT_DIR%"

title GitSonar - One Click Build
echo [GitSonar] Building EXE and installer...
echo.
powershell -ExecutionPolicy Bypass -NoLogo -File "%SCRIPT_DIR%build_setup.ps1"
set "EXIT_CODE=%ERRORLEVEL%"
echo.

if not "%EXIT_CODE%"=="0" (
  echo Build failed. See the error output above.
) else (
  echo Build complete.
  echo EXE: artifacts\dist\GitSonar.exe
  echo Installer: artifacts\dist\installer\GitSonarSetup.exe
)

echo.
pause
exit /b %EXIT_CODE%
