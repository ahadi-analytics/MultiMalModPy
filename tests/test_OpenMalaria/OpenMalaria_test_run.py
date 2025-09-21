import logging
import manifest
import os
import subprocess
import shutil

# Construct OpenMalaria base path
openmalaria_dir = os.path.join(manifest.ROOT_DIR, 'dependencies', 'OpenMalaria', f'om_v{manifest.openmalaria_version}')
openmalaria_exe = os.path.join(openmalaria_dir, 'openMalaria.exe')

# Define job directory (working directory for running the job)
job_directory = os.path.join(manifest.ROOT_DIR, 'tests')

# Files to copy and later remove
required_files = [
    "example_scenario.xml",
    "densities.csv",
    f"scenario_{manifest.openmalaria_version}.xsd"
]

# Copy files
copied_paths = []
for file in required_files:
    src = os.path.join(openmalaria_dir, file)
    dst = os.path.join(job_directory, file)
    shutil.copy(src, dst)
    copied_paths.append(dst)

# Define and run command
command = [openmalaria_exe, "--scenario", "example_scenario.xml"]
result = subprocess.run(command, capture_output=True, text=True, cwd=job_directory)

# Output
print("STDOUT:")
print(result.stdout)
print("STDERR:")
print(result.stderr)

# Clean up: delete copied files
for path in copied_paths:
    try:
        os.remove(path)
    except Exception as e:
        logging.warning(f"Failed to delete {path}: {e}")
