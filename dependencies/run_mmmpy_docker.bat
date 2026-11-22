@echo off
setlocal
REM Check if Docker is installed
where docker >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo Docker is not installed. Please install Docker first.
    pause
    exit /b 1
)

REM Pull the Docker image
docker pull multimalmodpy/mmmpy_local:rocky8
if errorlevel 1 (
    echo Docker image download failed. Check that Docker Desktop is running.
    pause
    exit /b 1
)

REM Ask the user for model names
set /p "MODELS=Enter models to run (e.g. malariasimulation OpenMalaria): "

REM Resolve the repository relative to this script.
for %%i in ("%~dp0..") do set "REPO_PATH=%%~fi"

REM Display what will run
echo Running Docker with models: %MODELS%
echo Mounting %REPO_PATH% to /mnt/c/projects/MultiMalModPy

REM Escape the MODELS variable for safe injection into bash command
REM We surround %MODELS% with double quotes inside single quotes to preserve spacing

docker run -it --rm ^
  -v "%REPO_PATH%:/mnt/c/projects/MultiMalModPy" ^
  multimalmodpy/mmmpy_local:rocky8 ^
  /bin/bash -c "source /opt/envs/mmmpy_local/bin/activate && cd /mnt/c/projects/MultiMalModPy && python launch_sim.py --models %MODELS% --test"

set "RUN_EXIT_CODE=%ERRORLEVEL%"
echo.
pause
exit /b %RUN_EXIT_CODE%