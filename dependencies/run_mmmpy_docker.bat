@echo off
REM Check if Docker is installed
where docker >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo Docker is not installed. Please install Docker first.
    pause
    exit /b
)

REM Pull the Docker image
docker pull multimalmodpy/mmmpy_local:rocky8

REM Ask the user for model names
set /p "MODELS=Enter models to run (e.g. malariasimulation OpenMalaria): "

REM Get two levels up from current directory
for %%i in ("%cd%\..\..") do set "REPO_PATH=%%~fi"

REM Display what will run
echo Running Docker with models: %MODELS%
echo Mounting %REPO_PATH% to /mnt/c/projects

REM Escape the MODELS variable for safe injection into bash command
REM We surround %MODELS% with double quotes inside single quotes to preserve spacing

docker run -it --rm ^
  -v "%REPO_PATH%:/mnt/c/projects" ^
  multimalmodpy/mmmpy_local:rocky8 ^
  /bin/bash -c "source /opt/envs/mmmpy_local/bin/activate && cd /mnt/c/projects/MultiMalModPy && python launch_sim.py --models %MODELS% --test"

echo.
pause

