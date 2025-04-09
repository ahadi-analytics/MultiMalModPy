import os.path

from utility.helper import *

def submit_analyze_outputs(exp, t='01:00:00', memG=10):
    """
    Submits a job to analyze malaria simulation outputs using SLURM.

    This function generates a shell script to run the analysis and submits it to the SLURM workload manager
    with dependencies on a specified job.

    Args:
        exp (Experiment): An instance of the Experiment class containing job configuration and directories.
        t (str, optional): Time limit for the job in HH:MM:SS format. Defaults to '01:00:00'.
        memG (int, optional): Memory allocation in GB for the job. Defaults to 4.

    Returns:
        None: This function does not return any value. It only submits the job and prints the job ID.
    """

    header_post = shell_header_quest(exp.sh_hpc_config, t, memG, job_name='analyze_malariasimulation',
                                     mem_scl=exp.mem_increase_factor)

    pycommand = f'\ncd {exp.root_directory}/malariasimulation' \
                f'\n{exp.EMOD_venv}' \
                f'\npython analyze_sim.py --dir "{exp.job_directory}"'

    script_path = os.path.join(exp.job_directory, 'run_analyzer_malariasimulation.sh')
    file = open(script_path, 'w')
    file.write(header_post + pycommand)
    file.close()

    malariasimulation_job_path = os.path.join(exp.job_directory, 'job_id_malariasimulation.txt')
    job_id = open(malariasimulation_job_path).read().strip()

    p = subprocess.run(['sbatch', '--parsable', f'--dependency=afterany:{job_id}', script_path], stdout=subprocess.PIPE,
                       cwd=str(exp.job_directory))

    slurm_job_id = p.stdout.decode('utf-8').strip().split(' ')[-1]
    print(f'Submitted analyzer for malariasimulation  - job id: {slurm_job_id}')
    write_txt(slurm_job_id, exp.job_directory, 'job_id_malariasimulation_analyze.txt')


def submit_run_malariasimulation(exp):
    """
    Submits a malariasimulation job for execution on different platforms.

    This function prepares the necessary scripts and submits the malariasimulation job based on the specified HPC configuration.
    If the job is to be run locally, it generates the required PowerShell script for running malariasimulation and submits
    it for execution. For SLURM-based jobs, it delegates the submission to the SLURM-specific function.

    Args:
        exp (object): An experiment object containing attributes like 'job_directory', 'hpc', 'analyzer_script',
                      and 'malariasimulation_jobs' needed for job configuration and submission.

    Raises:
        ValueError: If an unsupported HPC configuration is provided.
        subprocess.CalledProcessError: If there is an issue with running the job submission command for SLURM.
    """
    os.makedirs(os.path.join(exp.job_directory, 'malariasimulation_jobs'), exist_ok=True)

    if exp.hpc == 'LOCAL':
        if not exp.use_container:
            from utility.helper_local import write_ps1_analyzer, submit_runmodel_local
            write_ps1_malariasimulation(exp)
            write_ps1_analyzer(exp, pyscript=exp.analyzer_script[0], model_to_run='malariasimulation')
            submit_runmodel_local(exp, model_to_run='malariasimulation')
        else:
            from utility.helper_local_docker import write_sh_analyzer, write_sh_plotters, submit_runmodel_sh
            write_sh_malariasimulation(exp)
            write_sh_analyzer(exp, pyscript=exp.analyzer_script[0], model_to_run='malariasimulation')
            #write_sh_plotters(exp, model_to_run='malariasimulation')
            submit_runmodel_sh(exp, model_to_run='malariasimulation')
    else:
        # Default, run via SLURM on HPC
        submit_run_malariasimulation_slurm(exp)

def submit_run_malariasimulation_slurm(exp):
    """
    Submits a SLURM array job to run malaria simulations using an R script.

    This function generates a shell script to execute the malaria simulation for a specified number of experiments
    and submits it to the SLURM workload manager. It also triggers the submission of an analysis job after the
    simulations are submitted.

    Args:
        exp (Experiment): An instance of the Experiment class containing job configuration and directories.

    Returns:
        None: This function does not return any value. It submits the job and prints the job ID.
    """

    array = f'#SBATCH --array=1-{str(exp.nexps)}%{str(exp.max_running_jobs)}\n'
    header_post = shell_header_quest(exp.sh_hpc_config, exp.malariasimulation_time_per_sim, exp.malariasimulation_memory_per_sim, job_name='run_malariasimulation', arrayJob=array)
    ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

    r_file_path = os.path.join(ROOT_DIR, 'malariasimulation.R')
    script_path = os.path.join(exp.job_directory, 'run_malariasimulation.sh')
    malariasimulation_input_path = exp.malariasimulation_input_path
    slurmID = '${SLURM_ARRAY_TASK_ID}'

    # Set up script for submitting malariasimulation simulations as a SLURM array job
    # The command structure for running an R Script as a subprocess is:
    #    1) the command (which sets up that the file type is a Rscript)
    #    2) the path to the Rscript 
    #    3) the inputs we want in our Rscript
    file = open(script_path, 'w')
    file.write(header_post + f'\ncd {malariasimulation_input_path}')
    file.write(f'\nRscript {r_file_path} {ROOT_DIR} {exp.job_directory} {slurmID}')
    file.close()

    # Now we can run the rscript as a subprocess via sbatch
    p = subprocess.run(['sbatch', script_path], check=True, stdout=subprocess.PIPE, cwd=str(exp.job_directory))
    slurm_job_id = p.stdout.decode('utf-8').strip().split(' ')[-1]
    print(f'Submitted simulations for malariasimulation  - job id: {slurm_job_id}')

    write_txt(slurm_job_id, exp.job_directory, 'job_id_malariasimulation.txt')
    submit_analyze_outputs(exp)
    return

def write_ps1_malariasimulation(exp):
    """
    Creates a PowerShell script to run malariasimulation simulations (sequentially) locally.

    This function generates a PowerShell script that:
    1. Sets job parameters, including the path to the malariasimulation executable and the job directory.
    2. Ensures the log directory exists, creating it if necessary.
    3. Iterates over all experiments, running the malariasimulation for each one using the specified R script.
    4. Logs the output and errors to respective log files.

    Args:
        exp (object): An experiment object containing attributes such as 'job_directory', 'nexps', 'r_local', and paths
                      necessary for setting up and running the malariasimulation.

    Raises:
        IOError: If there is an issue with writing the PowerShell script to the file.
    """

    file_path = os.path.join(exp.job_directory, 'run_malariasimulation.ps1')  # Change file extension to .ps1
    wdir = os.path.abspath(os.path.dirname(__file__))
    wdir = os.path.abspath(os.path.join(wdir, os.pardir))

    # Define the content of the PowerShell script
    powershell_content = f"""
# Job settings
$job_name = "run_malariasimulation"
$exe_path = "{os.path.join(exp.r_local)}"
$work_dir = "{os.path.join(os.getcwd(),'malariasimulation')}"
$jobdir = "{exp.job_directory}"
$log_dir = Join-Path $jobdir "log"

# Navigate to the working directory
Set-Location -Path "$work_dir"

# Loop to run the malariasimulation command
for ($i = 1; $i -le {exp.nexps}; $i++) {{
    # Run the malariasimulation command
    & "$exe_path/Rscript.exe" "$work_dir\malariasimulation.R" "$work_dir" "$jobdir" $i >> "$log_dir/run_malariasimulation.log" 2>> "$log_dir/run_malariasimulation.err"
}}

# Pause to keep the console open
Write-Host "malariasimulation simulation complete."
    """

    # Write the PowerShell script
    with open(file_path, 'w') as file:
        file.write(powershell_content)
    print(f"PowerShell script written successfully at {file_path}")

def write_sh_malariasimulation(exp):
    """
    Creates a shell script to run malariasimulation simulations (sequentially) locally.

    This function generates a shell script that:
    1. Sets job parameters, including the path to the OpenMalaria executable and the job directory.
    2. Ensures the log directory exists, creating it if necessary.
    3. Iterates over all experiments, running the OpenMalaria simulation for each one.
    4. Logs the output and errors to respective log files.

    Args:
        exp (object): An experiment object containing attributes such as 'job_directory', 'nexps', and paths
                      necessary for setting up and running the simulation.

    Raises:
        IOError: If there is an issue with writing the shell script to the file.
    """
    # Define file path for shell script
    file_path = os.path.join(exp.job_directory, 'run_malariasimulation.sh')

    # Get the absolute path of the working directory
    wdir = os.path.abspath(os.path.dirname(__file__))
    wdir = os.path.abspath(os.path.join(wdir, os.pardir))

    # Construct the content of the shell script
    sh_content = f"""#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status
trap 'echo "Error occurred in script at line $LINENO. Check logs for details." >> "$log_dir/run_malariasimulation.err"; exit 1' ERR

# Job settings
job_name="run_malariasimulation"
work_dir="{os.path.normpath(os.path.join(os.getcwd(),'malariasimulation'))}"
jobdir="{os.path.normpath(exp.job_directory)}"
log_dir="$jobdir/log"

# Navigate to the working directory
cd $work_dir

# Create log directory if it doesn't exist
if [ ! -d "$log_dir" ]; then
    mkdir -p "$log_dir"
fi

# Run the OpenMalaria simulation for each experiment
for ((i = 1; i <= {exp.nexps}; i++)); do

    Rscript "$work_dir/malariasimulation.R" "$work_dir" "$jobdir" $i >> "$log_dir/run_malariasimulation.log" 2>> "$log_dir/run_malariasimulation.err"  &

    echo "Simulation $i completed successfully" >> "$log_dir/run_malariasimulation.log"
done

# Wait for all background jobs to finish
wait  

echo "All simulations completed successfully."
"""

    # Write the shell content to a .sh file
    with open(file_path, 'w') as file:
        file.write(sh_content)

    # Make script executable
    os.chmod(file_path, os.stat(file_path).st_mode | 0o111)
    print(f"Shell script written at {file_path}")
