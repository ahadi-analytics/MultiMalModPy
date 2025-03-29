import os
import subprocess
import stat
from datetime import datetime as dt


#### Running locally from inside docker
def exec(exp, command):

    process = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE,
                            universal_newlines=True, text=True, cwd=exp.job_directory)

    # Capture the output and errors
    stdout, stderr = process.communicate()

    # Print output and errors (if any)
    print("=== STDOUT ===")
    print(stdout)

    print("=== STDERR ===")
    if stderr:
        print(stderr)

        # Check if the process was successful
    if process.returncode != 0:
        print(f" Script failed with exit code {process.returncode}")
    else:
        print("️ Script completed successfully.")


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
    venv_activation = f"{exp.EMOD_venv}\n"

    # Generate the Python command to run the script
    pycommand = f'\npython {pyscript} -d {exp.sim_out_dir} {custom_args}'

    # Write the shell script to a file
    script_path = os.path.join(exp.job_directory, shname)
    print(f"Script written to {script_path}")

    with open(script_path, 'w') as file:
        file.write(header_post + venv_activation + f'\ncd {wdir}' + pycommand)

    # Make script executable
    os.chmod(script_path, os.stat(script_path).st_mode | 0o111)



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

def write_sh_plotters(exp, model_to_run):
    """
    This function generates a shell script that runs the specified analyzer script for the given model.
    The generated shell script will activate the virtual environment and run the Python script.

    Args:
        exp (object): An experiment object containing the 'job_directory' attribute for saving the script.
        pyscript (str): The path to the Python script to be run by the analyzer.
        model_to_run (str): The model name (e.g., 'OpenMalaria', 'malariasimulation') to customize the script for the specific model.

    Raises:
        ValueError: If the model name or script path is invalid, ensuring correct arguments are passed.
    """

    # Validate inputs
    if not model_to_run:
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
    job_name = f"analyze_{model_to_run}"
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
    py_args = f'--directory "{exp.sim_out_dir}" --modelname {model_to_run} '  # Custom directory argument for your script

    # Determine which plots to run
    plots_to_run = [p for p in exp.plots_to_run if not p == 'sampleplots']
    if exp.plots_to_run[0] == 'all':
        plots_to_run =  ['relationship', 'timeseries', 'agecurves']

    # Create shell scripts for each plot
    for plot_name in plots_to_run:
        pyscript_name = f'plot_{plot_name}.py'
        pycommand = f'python {pyscript_name} {py_args}\n'  # Command to run the Python script
        sh_content += f'\n# Run {plot_name}.py\n'
        sh_content += pycommand + f'>> "$log_dir/run_{plot_name}_openmalaria.log" 2>> "$log_dir/run_{plot_name}_openmalaria.err" & \n'

    # Write the shell script to a file
    with open(script_path, 'w', encoding='utf-8') as file:
        file.write(sh_content)

    # Make the shell script executable
    os.chmod(script_path, os.stat(script_path).st_mode | 0o111)
    print(f"Shell script written to {script_path}")


def write_sh_analyzer(exp, pyscript, model_to_run):
    """
    This function generates a shell script that runs the specified analyzer script for the given model.
    The generated shell script will activate the virtual environment and run the Python script.

    Args:
        exp (object): An experiment object containing the 'job_directory' attribute for saving the script.
        pyscript (str): The path to the Python script to be run by the analyzer.
        model_to_run (str): The model name (e.g., 'OpenMalaria', 'malariasimulation') to customize the script for the specific model.

    Raises:
        ValueError: If the model name or script path is invalid, ensuring correct arguments are passed.
    """

    # Validate inputs
    if not model_to_run:
        raise ValueError("Model name cannot be empty.")

    # Define the shell script filename and path
    shname = f'run_analyze_{model_to_run}.sh'
    script_path = os.path.join(exp.job_directory, shname)

    # Check that the job directory exists
    if not os.path.isdir(exp.job_directory):
        raise ValueError(f"Invalid job directory: {exp.job_directory}")

    # Prepare the shell script content
    sh_content = "#!/bin/bash\n\n"

    # Job settings
    job_name = f"analyze_{model_to_run}"
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

    # Set custom arguments and run the Python command
    py_args = f'--directory "{exp.job_directory}"'  # Custom directory argument for your script
    pycommand = f'python {pyscript} {py_args}\n'  # Command to run the Python script

    # Change to the appropriate directory and run the script
    sh_content += f'cd {os.path.join(exp.ROOT_DIR, model_to_run)}\n'
    sh_content += pycommand + '>> "$log_dir/run_analyzer_openmalaria.log" 2>> "$log_dir/run_analyzer_openmalaria.err"\n'

    # Write the shell script to a file
    with open(script_path, 'w', encoding='utf-8') as file:
        file.write(sh_content)

    # Make the shell script executable
    os.chmod(script_path, os.stat(script_path).st_mode | 0o111)

    print(f"Shell script written to {script_path}")


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
    echo "Running job 2: analyze_{modelname}.sh"
    {{
        # Run the second script: analyze_sim_{modelname}.sh
        bash "{os.path.normpath(os.path.join(exp.job_directory, 'run_analyze_' + modelname + '.sh'))}"
    }} || {{
        echo "Job 2 failed"
        exit 1
    }}

    echo "Job 2 completed successfully."

    # Start the third job (only after the second job completes)
    echo "Running job 3: plot_{modelname}.sh"
    {{
        # Run the third script: plot_{modelname}.sh
        bash "{os.path.normpath(os.path.join(exp.job_directory, 'run_plotters_' + modelname + '.sh'))}"
    }} || {{
        echo "Job 3 failed"
        exit 1
    }}

    echo "Job 3 completed successfully."
    
    echo "All jobs completed."
    read -p "Press Enter to close the terminal"
    """

    # Write the shell script to a file
    print(f"Shell script written to {filename}")
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(shell_content)

    # Make script executable
    os.chmod(filename, os.stat(filename).st_mode | 0o111)


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
    exec(exp, command=f"bash {file_path}")
