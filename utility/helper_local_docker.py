import os
import subprocess
import shlex
import stat
from datetime import datetime as dt


#### Running locally from inside docker
def exec(exp, command):
    """
    Executes a shell command in a subprocess, showing its output and errors in the terminal.
    This function runs the specified command within the given experiment's job directory,
    forwarding both standard output and error streams to the terminal. It also ensures the process runs in a
    separate session, preventing it from being terminated if the parent process exits.

    Args:
        exp (object): An object containing experiment-related attributes, including
            `job_directory`, which specifies the working directory for the command.
        command (str): The shell command to execute.

    Returns:
        None
    """

    # Show progress immediately and propagate a failed command to the launcher.
    subprocess.run(command, shell=True, cwd=exp.job_directory,
                   start_new_session=True, check=True)
    print("Script completed successfully.", flush=True)


def write_and_execute_sh_script(script_path: str, content: str, exp=None, execute: bool = False):
    """
    Writes a shell script to a file, makes it executable, and optionally executes it.

    Args:
        script_path (str): The full path where the shell script should be saved.
        content (str): The shell script content to write.
        exp (object, optional): Experiment configuration object, required if executing the script.
        execute (bool, optional): If True, executes the script after writing it. Default is False.
    """
    try:
        with open(script_path, "w", encoding="utf-8", newline="\n") as file:
            file.write(content)
        print(f"Shell script written to {script_path}")
    except OSError as e:
        raise OSError(f"Error writing shell script: {e}")

    # Make the script executable
    os.chmod(script_path, os.stat(script_path).st_mode | 0o111)

    # Optionally execute the script
    if execute:
        if exp is None:
            raise ValueError("Experiment object (exp) is required for script execution.")
        try:
            exec(exp, command=f"bash {shlex.quote(str(script_path))}")
        except Exception as e:
            raise RuntimeError(f"Error executing shell script: {e}")


def submit_run_pyscript_sh(exp, pyscript='plotter/plot_relationship.py', shname='run_relationship_plots.sh',
                           custom_args='--models EMOD malariasimulation OpenMalaria', wdir=None):
    """
    Generates a shell script to execute a Python script inside a Docker container
    and runs the shell script.

    This function:
    - Creates a Bash script that activates the virtual environment.
    - Changes to the correct working directory.
    - Runs the specified Python script with custom arguments.
    - Grants execution permissions to the script.
    - Executes the script inside the container using subprocess.

    Args:
        exp (object): Experiment configuration object, must have:
            - `EMOD_venv` (str): Virtual environment activation command.
            - `output_directory` (str): Simulation output directory.
            - `job_directory` (str): Directory where the shell script will be created.
        pyscript (str, optional): Path to the Python script to execute.
            Defaults to `"plotter/plot_relationship.py"`.
        shname (str, optional): Name of the generated shell script.
            Defaults to `"run_relationship_plots.sh"`.
        custom_args (str, optional): Custom command-line arguments for the Python script.
            Defaults to `"--models EMOD malariasimulation OpenMalaria"`.
        wdir (str, optional): Working directory for executing the script.
            If `None`, it defaults to the parent directory of the current file.

    Returns:
        None
    """

    # Validate experiment directory
    if not os.path.isdir(exp.job_directory):
        raise ValueError(f"Invalid job directory: {exp.job_directory}")

    # Determine working directory
    if wdir is None:
        wdir = os.path.abspath(os.path.dirname(__file__))
        wdir = os.path.abspath(os.path.join(wdir, os.pardir))

    # Shell script content
    sh_content = f"""#!/bin/bash
set -e -o pipefail

# Activate virtual environment
{exp.EMOD_venv}

# Change to the working directory
cd "{wdir}"

# Run the Python script with arguments
python "{pyscript}" -d "{exp.output_directory}" {custom_args}
"""

    # Define the shell script path
    script_path = os.path.join(exp.job_directory, shname)
    write_and_execute_sh_script(script_path=script_path, content=sh_content, exp=exp, execute=True)


def submit_run_plotters_sh(exp):
    """
    Creates shell scripts for running standardized plots inside a Docker container
    based on the models specified in the experiment.

    Args:
        exp (Experiment): The experiment object containing attributes such as
            `models` and `plots_to_run`, which determine which models and
            plots should be processed.

    Returns:
        list: List of paths to the generated shell scripts

    Notes:
        - The function checks which models are specified in `exp.models`
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
    if 'all' in exp.plots_to_run:
        plots_to_run = plot_names_all

    # Create shell scripts for each plot
    for plot_name in plots_to_run:
        # pyscript_name = f'-m plotter.plot_{plot_name}'
        pyscript_name = f'plot_{plot_name}.py'

        # Generate the shell script
        submit_run_pyscript_sh(exp, pyscript=pyscript_name, shname=f'run_{plot_name}_plots.sh',
                               custom_args=f"--models {' '.join([x for x in exp.models])}",
                               wdir=os.path.join(parent_dir, 'plotter'))


def write_sh_plotters(exp, model):
    """
    This function generates a shell script that runs the specified analyzer script for the given model.
    The generated shell script will activate the virtual environment and run the Python script.

    Args:
        exp (object): An experiment object containing the 'job_directory' attribute for saving the script.
        pyscript (str): The path to the Python script to be run by the analyzer.
        model (str): The model name (e.g., 'OpenMalaria', 'malariasimulation') to customize the script for the specific model.

    Raises:
        ValueError: If the model name or script path is invalid, ensuring correct arguments are passed.
    """

    # Validate inputs
    if not model:
        raise ValueError("Model name cannot be empty.")

    # Define the shell script filename and path
    shname = f'run_plotters_{model_to_run}.sh'
    script_path = os.path.join(exp.job_directory, shname)

    # Check that the job directory exists
    if not os.path.isdir(exp.job_directory):
        raise ValueError(f"Invalid job directory: {exp.job_directory}")

    # Prepare the shell script content
    sh_content = "#!/bin/bash\n\n"

    # Job settings
    job_name = f"analyze_{model}"
    sh_content += f"# Job settings\n"
    sh_content += f'job_name="{job_name}"\n'
    sh_content += f'jobdir="{exp.job_directory}"\n'
    sh_content += f'log_dir="$jobdir/log"\n\n'

    # Check if the log directory exists, create it if necessary
    sh_content += 'if [ ! -d "$log_dir" ]; then\n'
    sh_content += '    mkdir -p "$log_dir"\n'
    sh_content += 'fi\n\n'

    # Activate virtual environment (make sure it's available)
    venv_activation = f"{exp.EMOD_venv}\n"
    sh_content += f"# Activate virtual environment\n{venv_activation}\n"
    sh_content += f"# Set working directory\ncd {exp.ROOT_DIR}/plotter\n"

    # Set custom arguments and run the Python command
    py_args = f'--directory "{exp.output_directory}" --models {model} '  # Custom directory argument for your script

    # Determine which plots to run
    plots_to_run = [p for p in exp.plots_to_run if not p == 'sampleplots']
    if exp.plots_to_run[0] == 'all':
        plots_to_run = ['relationship', 'timeseries', 'agecurves']

    # Create shell scripts for each plot
    for plot_name in plots_to_run:
        pyscript_name = f'plot_{plot_name}.py'
        pycommand = f'python {pyscript_name} {py_args}\n'  # Command to run the Python script
        sh_content += f'\n# Run {plot_name}.py\n'
        sh_content += pycommand + f'>> "$log_dir/run_{plot_name}_openmalaria.log" 2>> "$log_dir/run_{plot_name}_openmalaria.err" & \n'

    # Write the shell script to a file
    write_and_execute_sh_script(script_path=script_path, content=sh_content, exp=exp, execute=False)


def write_sh_analyzer(exp, pyscript, model):
    """
    This function generates a shell script that runs the specified analyzer script for the given model.
    The generated shell script will activate the virtual environment and run the Python script.

    Args:
        exp (object): An experiment object containing the 'job_directory' attribute for saving the script.
        pyscript (str): The path to the Python script to be run by the analyzer.
        model (str): The model name (e.g., 'OpenMalaria', 'malariasimulation') to customize the script for the specific model.

    Raises:
        ValueError: If the model name or script path is invalid, ensuring correct arguments are passed.
    """

    # Validate inputs
    if not model:
        raise ValueError("Model name cannot be empty.")

    # Define the shell script filename and path
    shname = f'run_analyze_{model}.sh'
    script_path = os.path.join(exp.job_directory, shname)

    # Check that the job directory exists
    if not os.path.isdir(exp.job_directory):
        raise ValueError(f"Invalid job directory: {exp.job_directory}")

    # Prepare the shell script content
    sh_content = "#!/bin/bash\nset -e -o pipefail\n\n"

    # Job settings
    job_name = f"analyze_{model}"
    sh_content += f"# Job settings\n"
    sh_content += f'job_name="{job_name}"\n'
    sh_content += f'jobdir="{exp.job_directory}"\n'
    sh_content += f'log_dir="$jobdir/log"\n\n'

    # Check if the log directory exists, create it if necessary
    sh_content += 'if [ ! -d "$log_dir" ]; then\n'
    sh_content += '    mkdir -p "$log_dir"\n'
    sh_content += 'fi\n\n'

    # Activate virtual environment (make sure it's available)
    venv_activation = f"{exp.EMOD_venv}\n"
    sh_content += f"# Activate virtual environment\n{venv_activation}\n"

    # Only malariasimulation supports the parameter-variation analyzer.
    py_args = f'--directory "{exp.job_directory}"'
    flags = ['']
    if model == 'malariasimulation':
        variation = exp.malariasimulation_parameter_variation
        if variation not in ('no', 'yes', 'both'):
            raise ValueError(f'Invalid parameter variation mode: {variation}')
        flags = {'no': [''], 'yes': [' --mpv'], 'both': ['', ' --mpv']}[variation]

    sh_content += f'cd "{os.path.join(exp.ROOT_DIR, model)}"\n'
    for flag in flags:
        sh_content += (f'echo "Running {model} analyzer{flag}; logs: $log_dir"\n'
                       f'python "{pyscript}" {py_args}{flag} '
                       f'>> "$log_dir/run_analyzer_{model}.log" '
                       f'2>> "$log_dir/run_analyzer_{model}.err"\n')

    # Write the shell script to a file
    write_and_execute_sh_script(script_path=script_path, content=sh_content, exp=exp, execute=False)


def write_sh_runmodel(exp, filename, model):
    """
    Writes a PowerShell script that manages the execution of two jobs:
    1. Runs the first script (e.g., run_{model}.sh)
    2. Runs the second script (e.g., analyze_sim_{model}.sh) after the first completes

    Args:
        exp (Experiment): The experiment object that contains job directories and other parameters.
        filename (str): The full path where the PowerShell script should be saved.
        model (str): The name of the model to run (e.g., 'malariasimulation', 'OpenMalaria').

    Raises:
        ValueError: If the provided model is empty or if exp.job_directory is not valid.

    Returns:
        None: This function does not return a value but writes the PowerShell script to the specified file.
    """

    # Check for valid model and experiment directory
    if not model:
        raise ValueError("model cannot be empty.")

    if not os.path.isdir(exp.job_directory):
        raise ValueError(f"Invalid job directory: {exp.job_directory}")

    # Define the shell script content
    sh_content = f"""#!/bin/bash
set -e -o pipefail

    # Start the first job
    echo "Running job 1: run_{model}.sh"
    {{
        # Run the first script: run_{model}.sh
        bash "{os.path.normpath(os.path.join(exp.job_directory, 'run_' + model + '.sh'))}"
    }} || {{
        echo "Simulation failed; analysis skipped. See {exp.job_directory}/log" >&2
        exit 1
    }}

    echo "Job 1 completed successfully."

    # Start the second job (only after the first job completes)
    echo "Running job 2: analyze_{model}.sh"
    {{
        # Run the second script: analyze_sim_{model}.sh
        bash "{os.path.normpath(os.path.join(exp.job_directory, 'run_analyze_' + model + '.sh'))}"
    }} || {{
        echo "Analysis failed. See {exp.job_directory}/log/run_analyzer_{model}.err" >&2
        exit 1
    }}

    echo "Job 2 completed successfully."

    # Start the third job (only after the second job completes)
    #echo "Running job 3: plot_{model}.sh"
    #{{
    #    # Run the third script: plot_{model}.sh
    #    bash "{os.path.normpath(os.path.join(exp.job_directory, 'run_plotters_' + model + '.sh'))}"
    #}} || {{
    #    echo "Job 3 failed"
    #    exit 1
    #}}
    #
    #echo "Job 3 completed successfully."
    
    echo "All jobs completed."
    """

    # Write the shell script to a file
    write_and_execute_sh_script(script_path=filename, content=sh_content, exp=exp, execute=False)


def submit_runmodel_sh(exp, model):
    """
    This function creates a PowerShell script for running the specified model, saves it in the specified job directory,
    and then executes the script using the 'cmd.exe' command.

    Args:
        exp (object): An experiment object containing the 'job_directory' attribute where the PowerShell script will be saved.
        model (str): The name of the model to be run (e.g., 'OpenMalaria', 'malariasimulation').

    Raises:
        OSError: If there is an issue with executing the command or running the script.
    """

    # Generate shell script name
    file_name = f'jobs_{model}_simplerun.sh'
    file_path = os.path.join(exp.job_directory, file_name)

    # Assuming `create_shell_script` is the function from the previous response
    write_sh_runmodel(exp, filename=file_path, model=model)

    # Execute the generated shell script using subprocess
    exec(exp, command=f"bash {shlex.quote(file_path)}")