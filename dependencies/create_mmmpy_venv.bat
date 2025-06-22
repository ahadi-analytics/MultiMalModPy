@echo off

REM Check if python is installed
where python >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH.
    pause
    exit /b
)

REM Get project root directory (one level up from dependencies)
for %%i in ("%cd%\..") do set "PROJECT_ROOT=%%~fi"

echo Project root detected as: %PROJECT_ROOT%

REM Path to requirements.txt inside dependencies
set "REQ_FILE=%cd%\requirements.txt"

REM Ask user for venv folder name
set /p "VENV_NAME=Enter name for the virtual environment folder (default: venv): "

REM Use default if empty
if "%VENV_NAME%"=="" set "VENV_NAME=venv"

echo Creating virtual environment named: %VENV_NAME%

REM Create virtual environment inside project root with user name
python -m venv "%PROJECT_ROOT%\%VENV_NAME%"

REM Activate the virtual environment
call "%PROJECT_ROOT%\%VENV_NAME%\Scripts\activate.bat"

REM Upgrade pip
python -m pip install --upgrade pip

REM Install packages from requirements.txt inside dependencies
pip install -r "%REQ_FILE%"

echo.
echo NOTE: Some packages may fail to install if your Python version is incompatible or if packages are unavailable.
echo This is expected for certain dependencies. Please check the logs above if you experience issues.
echo.
echo Installation of virtual python environment complete.
pause
