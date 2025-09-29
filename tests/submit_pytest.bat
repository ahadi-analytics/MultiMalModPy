REM Run pytest inside Docker
pushd "%~dp0..\.." >nul
set "REPO_PATH=%CD%"
popd >nul

REM Convert to Docker path
set "DOCKER_PATH=%REPO_PATH:C:=/c%"
set "DOCKER_PATH=%DOCKER_PATH:\=/%"

echo Mounting %DOCKER_PATH% to /mnt/c/projects

docker run -it --rm ^
  -v "%DOCKER_PATH%:/mnt/c/projects" ^
  mrm9534/mmmpy_local:rocky8 ^
  /bin/bash -c "source /opt/envs/mmmpy_container/bin/activate && cd /mnt/c/projects/MultiMalModPy && pytest -v tests"

pause
