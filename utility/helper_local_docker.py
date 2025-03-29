import os
import subprocess
import stat
from datetime import datetime as dt


#### Running locally from inside docker
def exec(command, wdir=None):
    if wdir is None:
        wdir = os.getcwd()

    env = os.environ.copy()
    env["PYTHONPATH"] = "/mnt/c/projects/MultiMalModPy:" + env.get("PYTHONPATH", "")

    return subprocess.Popen(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE,
                            universal_newlines=True, text=True, cwd=wdir, env=env)


def submit_run_pyscript_sh(exp, pyscript='plotter/plot_relationship.py', shname='run_relationship_plots.sh',
                           custom_args='--modelname EMOD malariasimulation OpenMalaria', wdir=None):
    """
    Generate a shell script and execute it inside the Docker container

    Args:
        exp: Experiment configuration object
        pyscript: Python script to run
        shname: Shell script name
        custom_args: Custom command line arguments
        wdir: Working directory
    """
    # Get the current working directory
    if wdir is None:
        wdir = os.path.abspath(os.path.dirname(__file__))
        wdir = os.path.abspath(os.path.join(wdir, os.pardir))

    # Generate the shell script header
    header_post = "#!/bin/bash\n"

    # Activate virtual environment within container
    venv_activation = "source /opt/envs/mmmpy_container/bin/activate\n"

    # Generate the Python command to run the script
    pycommand = f'\npython {pyscript} -d {exp.sim_out_dir} {custom_args}'

    # Write the shell script to a file
    script_path = os.path.join(exp.job_directory, shname)
    with open(script_path, 'w') as file:
        file.write(header_post + venv_activation + f'\ncd {wdir}' + pycommand)

    # Make script executable
    os.chmod(script_path, os.stat(script_path).st_mode | 0o111)

    # Execute the script directly using subprocess
    print(f"Running: {shname}")

    subprocess.Popen(
        f"bash {script_path}",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=exp.job_directory
    )


def submit_run_plotters_sh(exp):
    """
    Creates shell scripts for running standardized plots inside a Docker container
    based on the models specified in the experiment.

    Args:
        exp (Experiment): The experiment object containing attributes such as
            `models_to_run` and `plots_to_run`, which determine which models and
            plots should be processed.

    Returns:
        list: List of paths to the generated shell scripts

    Notes:
        - The function checks which models are specified in `exp.models_to_run`
        - It creates shell scripts for default plots (`relationship`, `timeseries`, `agecurves`)
          and custom plots if specified in `exp.plots_to_run`
        - If `exp.plots_to_run` is set to `'all'`, all available plots will be processed
        - Each script can be run inside a Docker container
    """
    plot_names_all = ['relationship', 'timeseries', 'agecurves']

    # Get directory paths
    fdir = os.path.abspath(os.path.dirname(__file__))
    parent_dir = os.path.abspath(os.path.join(fdir, os.pardir))

    # Determine which plots to run
    plots_to_run = [p for p in exp.plots_to_run if not p == 'sampleplots']
    if exp.plots_to_run[0] == 'all':
        plots_to_run = plot_names_all

    # Create shell scripts for each plot
    for plot_name in plots_to_run:
        # pyscript_name = f'-m plotter.plot_{plot_name}'
        pyscript_name = f'plotter/plot_{plot_name}.py'

        # Generate the shell script
        submit_run_pyscript_sh(exp, pyscript=pyscript_name, shname=f'run_{plot_name}_plots.sh',
                               custom_args=f"--modelname {' '.join([x for x in exp.models_to_run])}", wdir=parent_dir)


def write_sh_analyzer(exp, pyscript, model_to_run):
    """
    This function generates a batch file that runs the specified analyzer script for the given model.
    It calls the `create_ps1_script` function to generate the PowerShell script file.

    Args:
        exp (object): An experiment object containing the 'job_directory' attribute for saving the script.
        pyscript (str): The path to the Python script to be run by the analyzer.
        model_to_run (str): The model name (e.g., 'OpenMalaria', 'malariasimulation') to customize the script for the specific model.

    Raises:
        ValueError: If the model name or script path is invalid, ensuring correct arguments are passed.
    """
    job_name = f"analyzer_{model_to_run}"
    subdir = model_to_run
    py_command = f'python {pyscript} --directory "{exp.job_directory}"'
    fname = f'run_analyze_{model_to_run}.sh'

    submit_run_pyscript_sh(exp, fname, subdir, job_name, py_command)


def write_sh_runmodel(exp, filename, modelname):
    """
    Writes a PowerShell script that manages the execution of two jobs:
    1. Runs the first script (e.g., run_{modelname}.sh)
    2. Runs the second script (e.g., analyze_sim_{modelname}.sh) after the first completes

    Args:
        exp (Experiment): The experiment object that contains job directories and other parameters.
        filename (str): The full path where the PowerShell script should be saved.
        modelname (str): The name of the model to run (e.g., 'malariasimulation', 'OpenMalaria').

    Raises:
        ValueError: If the provided modelname is empty or if exp.job_directory is not valid.

    Returns:
        None: This function does not return a value but writes the PowerShell script to the specified file.
    """

    # Check for valid modelname and experiment directory
    if not modelname:
        raise ValueError("Modelname cannot be empty.")

    if not os.path.isdir(exp.job_directory):
        raise ValueError(f"Invalid job directory: {exp.job_directory}")

    # Define the shell script content
    shell_content = f"""#!/bin/bash

    # Start the first job
    echo "Running job 1: run_{modelname}.sh"
    {{
        # Run the first script: run_{modelname}.sh
        bash "{os.path.normpath(os.path.join(exp.job_directory, 'run_' + modelname + '.sh'))}"
    }} || {{
        echo "Job 1 failed"
        exit 1
    }}

    echo "Job 1 completed successfully."

    # Start the second job (only after the first job completes)
    echo "Running job 2: analyze_sim_{modelname}.sh"
    {{
        # Run the second script: analyze_sim_{modelname}.sh
        bash "{os.path.normpath(os.path.join(exp.job_directory, 'run_analyze_' + modelname + '.sh'))}"
    }} || {{
        echo "Job 2 failed"
        exit 1
    }}

    echo "Job 2 completed successfully."

    echo "All jobs completed."
    read -p "Press Enter to close the terminal"
    """

    # Write the shell script to a file
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(shell_content)

    # Make script executable
    os.chmod(filename, os.stat(filename).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    print(f"Shell script has been written to {filename}")


def submit_runmodel_sh(exp, model_to_run):
    """
    This function creates a PowerShell script for running the specified model, saves it in the specified job directory,
    and then executes the script using the 'cmd.exe' command.

    Args:
        exp (object): An experiment object containing the 'job_directory' attribute where the PowerShell script will be saved.
        model_to_run (str): The name of the model to be run (e.g., 'OpenMalaria', 'malariasimulation').

    Raises:
        OSError: If there is an issue with executing the command or running the script.
    """

    # Generate shell script name
    file_name = f'jobs_{model_to_run}_simplerun.sh'
    file_path = os.path.join(exp.job_directory, file_name)

    # Assuming `create_shell_script` is the function from the previous response
    write_sh_runmodel(exp, filename=file_path, modelname=model_to_run)

    # Execute the generated shell script using subprocess
    cmd_command = f'bash "{file_path}"'
    process = subprocess.Popen(
        f"bash {file_path}",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Capture the output and errors
    stdout, stderr = process.communicate()

    # Print output and errors (if any)
    print("=== STDOUT ===")
    print(stdout)

    print("=== STDERR ===")
    if stderr:
        print(stderr)  # Print errors in red (if available)

    # Check if the process was successful
    if process.returncode != 0:
        print(f" Script failed with exit code {process.returncode}")
    else:
        print("️ Script completed successfully.")



def write_bat_submission_plots(exp):
    """
    Writes a .bat submission script to execute Python plotting commands for an experiment.

    Args:
        exp (Experiment): The experiment object containing the necessary directories and model names.
        filename (str): The file path where the batch script will be saved.

    Returns:
        None
    """
    # Extract relevant data from the experiment object
    wdir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    filename = 'submit_run_plots.bat'
    work_dir = wdir
    jobdir = exp.job_directory
    log_dir = f"{jobdir}\\log"
    models = ' '.join(exp.models_to_run)

    # List of plot scripts to run
    plot_scripts = [f'plot_{x}.py' for x in exp.plots_to_run]

    # Start creating the batch script content
    bat_content = f"@echo on\n"
    bat_content += f"set job_name=run_plot_all\n"
    bat_content += f"set work_dir={work_dir}\n"
    bat_content += f"set jobdir={jobdir}\n"
    bat_content += f"set log_dir=%jobdir%\\log\n\n"
    bat_content += f'cd /d "%work_dir%\\plotter"\n\n'

    # Add commands to run the plotting scripts
    for script in plot_scripts:
        plot_name = script.replace('.py', '')
        bat_content += f'docker run -it -v {exp.ROOT_DIR_local}:/mnt/c/projects {exp.image_path} /bin/bash -c "{exp.EMOD_venv_container} && python /mnt/c/projects/MultiMalModPy/{script}  --directory {exp.sim_out_dir} --modelname  {models} >> %log_dir%/run_{plot_name}.log 2>> %log_dir%/run_{plot_name}.err"'

    # Add pause at the end to keep the terminal open
    bat_content += "\nPause to keep the console open\n"
    bat_content += "pause\n"

    # Write the content to the batch file
    with open(os.path.join(exp.job_directory, filename), 'w') as file:
        file.write(bat_content)

    print(f"Batch script written to {os.path.join(exp.job_directory, filename)}")
