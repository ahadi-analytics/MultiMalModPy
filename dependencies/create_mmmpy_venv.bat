@echo off
REM Check if python is installed
where python >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH.
    pause
    exit /b
)

REM Get project root directory (one level up from current directory)
for %%i in ("%cd%\..") do set "PROJECT_ROOT=%%~fi"
echo Project root detected as: %PROJECT_ROOT%

REM Path to requirements.txt
set "REQ_FILE=%cd%\requirements_local.txt"

REM Ask user for venv folder name
set /p "VENV_NAME=Enter name for the virtual environment folder (default: venv): "
if "%VENV_NAME%"=="" set "VENV_NAME=venv"
echo Creating virtual environment named: %VENV_NAME%

REM Create virtual environment inside project root
python -m venv "%PROJECT_ROOT%\%VENV_NAME%"

REM Activate the virtual environment
call "%PROJECT_ROOT%\%VENV_NAME%\Scripts\activate.bat"

REM Upgrade pip
python -m pip install --upgrade pip

REM Install packages one by one and continue on errors
for /f "usebackq tokens=*" %%p in ("%REQ_FILE%") do (
    echo Installing package: %%p
    python -m pip install "%%p" --extra-index-url=https://packages.idmod.org/api/pypi/pypi-production/simple
    if ERRORLEVEL 1 (
        echo Failed to install: %%p
    )
)

echo.
echo NOTE: Some packages may fail to install if your Python version is incompatible or unavailable.
echo Please check the logs above for any failures.
echo Installation of virtual environment complete.
pause
