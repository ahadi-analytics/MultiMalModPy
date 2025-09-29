@echo off
REM -------------------------------
REM Download and extract OpenMalaria
REM -------------------------------

REM Set version number (modify for newer releases)
SET version=46

REM Get project root (one level up)
for %%i in ("%cd%\..") do set "PROJECT_ROOT=%%~fi"
echo Project root detected as: %PROJECT_ROOT%

REM URL for OpenMalaria ZIP
SET URL=https://github.com/SwissTPH/openmalaria/releases/download/schema-%version%.0/openMalaria-windows.zip

REM Paths for download and extraction
SET DEST=%cd%\openMalaria-windows.zip
SET OUT_DIR=%cd%\om_v%version%

REM Create output directory if it doesn't exist
if not exist "%OUT_DIR%" mkdir "%OUT_DIR%"

echo Downloading OpenMalaria v%version% (modify .bat file for newer versions)...
powershell -Command "Invoke-WebRequest -Uri '%URL%' -OutFile '%DEST%'"

echo Extracting OpenMalaria to a temporary folder...
SET TMP_DIR=%cd%\temp_openMalaria
if not exist "%TMP_DIR%" mkdir "%TMP_DIR%"
powershell -Command "Expand-Archive -Path '%DEST%' -DestinationPath '%TMP_DIR%' -Force"

echo Moving contents to %OUT_DIR%...
xcopy /E /I /Y "%TMP_DIR%\openMalaria-windows\*" "%OUT_DIR%\" >nul

REM Remove temporary folder
rmdir /S /Q "%TMP_DIR%"

echo.
echo OpenMalaria v%version% has been downloaded and extracted to:
echo %OUT_DIR%
pause
