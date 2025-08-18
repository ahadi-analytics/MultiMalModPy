import os
import subprocess
from datetime import datetime as dt


class LoadLaunchArgs:
    """
    A class to represent and manage the argument settings for an experiment setup in MultiMalModPy.

    This class allows for initialization of various experiment parameters with default values, which can be
    overridden by user-provided values during object instantiation. It also provides methods to update the
    arguments after instantiation and to represent the current argument settings as a string.

    Attributes:
        directory (str or None): Directory where data is stored or to be saved.
        suite (str): The name of the suite, default is a string with the current date.
        expname (str): The name of the experiment, default is a string with the current time.
        emodstep (str or None): The EMOD step name.
        serializedid (str): A serialized identifier for the experiment.
        models (list of str): A list of models to be used in the experiment, default includes 'OpenMalaria' and 'malariasimulation'.
        user (str): The username of the person running the experiment, fetched from the environment.
        csv (str or None): CSV file for input data, if applicable.
        rownum (int or None): Row number in the CSV, if applicable.
        run_mode (str or None): The mode in which to run the simulation.
        emod_calib_params (bool): Whether to enable EMOD calibration parameters, default is False.
        overwrite (bool): Whether to overwrite existing files, default is False.
        mpv (bool): Whether to use MPV (most probable value), default is True.
        target_output_name (str): The type of output expected, default is 'prevalence_2to10'.

    Methods:
        __init__(**kwargs): Initializes the Args object with default values, which can be overridden by user-provided values.
        update(**kwargs): Updates the Args object with new values after initialization.
        __repr__(): Returns a string representation of the current argument settings.

    Args:
        kwargs (dict): Optional keyword arguments to override default argument values during initialization.

    """

    def __init__(self, **kwargs):
        """
        Initialize the Args object with default values.
        User-provided values can override these defaults.
        """
        from datetime import datetime as dt
        # Default values
        self.directory = None
        self.suite = f'test_{dt.now().strftime("%Y%m%d")}'
        self.expname = f'sims_entomologymode_seasonality_intervention_{dt.now().strftime("%H_%M_%S")}'
        self.emodstep = None
        self.serializedid = ''
        self.models = ['OpenMalaria', 'malariasimulation']  # 'EMOD'
        self.user = os.environ.get('USER')
        self.csv = None
        self.rownum = None
        self.run_mode = 'custom'
        self.emod_calib_params = False
        self.overwrite = False
        self.mpv = True
        self.test = True
        self.note = ''
        self.target_output_name = 'prevalence_2to10'

        # Update with any user-provided values
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def update(self, **kwargs):
        """
        Update the Args object with new values.
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self):
        """
        Return a string representation of the current argument settings.
        """
        return (f"Args(directory={self.directory}, suite={self.suite}, expname={self.expname}, "
                f"emodstep={self.emodstep}, serializedid={self.serializedid}, models={self.models}, "
                f"user={self.user}, csv={self.csv},  rownum={self.rownum}, "
                f"run_mode={self.run_mode}, emod_calib_params={self.emod_calib_params}, "
                f"overwrite={self.overwrite}, mpv={self.mpv}, test={self.test}, note={self.note}, target_output_name={self.target_output_name})")


def write_ps1_runmodel(exp, filename, model):
    """
    Writes a PowerShell script that manages the execution of two jobs:
    1. Runs the first script (e.g., run_{models}.ps1)
    2. Runs the second script (e.g., analyze_sim_{models}.ps1) after the first completes

    Args:
        exp (Experiment): The experiment object that contains job directories and other parameters.
        filename (str): The full path where the PowerShell script should be saved.
        model (str): The name of the model to run (e.g., 'malariasimulation', 'OpenMalaria').

    Raises:
        ValueError: If the provided models is empty or if exp.job_directory is not valid.

    Returns:
        None: This function does not return a value but writes the PowerShell script to the specified file.
    """

    # Check for valid models and experiment directory
    if not model:
        raise ValueError("model cannot be empty.")

    if not os.path.isdir(exp.job_directory):
        raise ValueError(f"Invalid job directory: {exp.job_directory}")

    ps1_content = f"""
    # Start logging to a file
    $LogFile = {{ {os.path.normpath(os.path.join(exp.job_directory, 'log'))}\\run_{model}.out }}
    Start-Transcript -Path $LogFile
    
    # Start the first job
    $job1 = Start-Job -ScriptBlock {{
        try {{
            # Run the first script: run_{model}.ps1
            Write-Host "Running job 1: run_{model}.ps1"
            & "{os.path.normpath(exp.job_directory)}\\run_{model}.ps1"
        }} catch {{
            Write-Error "Job 1 failed: $_"
        }}
    }}

    # Wait for the first job to complete
    Receive-Job -Job $job1 -Wait
    if ($job1.State -eq 'Completed') {{
        Write-Host "Job 1 completed successfully."
    }} else {{
        Write-Error "Job 1 did not complete successfully."
    }}
    $job1 | Remove-Job
    Stop-Transcript
    

    # Start the second job (only after the first job completes)
    $LogFile = {{ {os.path.normpath(os.path.join(exp.job_directory, 'log'))}\\run_analyzer_{model}.out }}
    Start-Transcript -Path $LogFile
    
    $job2 = Start-Job -ScriptBlock {{
        try {{
            # Run the second script with -ExecutionPolicy Bypass and explicit -File parameter
            Write-Host "Running job 2: analyze_sim_{model}.ps1"
            & "powershell.exe" -ExecutionPolicy Bypass -File "{os.path.normpath(exp.job_directory)}\\run_analyze_{model}.ps1"
        }} catch {{
            Write-Error "Job 2 failed: $_"
        }}
    }}

    # Wait for the second job to complete
    Receive-Job -Job $job2 -Wait
    if ($job2.State -eq 'Completed') {{
        Write-Host "Job 2 completed successfully."
    }} else {{
        Write-Error "Job 2 did not complete successfully."
    }}
    $job2 | Remove-Job

    Write-Host "All jobs completed."
    Stop-Transcript
        
    Read-Host "Press Enter to close the terminal"
    """

    # Write to the specified file
    with open(filename, 'w') as file:
        file.write(ps1_content)

    print(f"PowerShell script has been written to {filename}")


def submit_runmodel_local(exp, model):
    """
    This function creates a PowerShell script for running the specified model, saves it in the specified job directory,
    and then executes the script using the 'cmd.exe' command.

    Args:
        exp (object): An experiment object containing the 'job_directory' attribute where the PowerShell script will be saved.
        model (str): The name of the model to be run (e.g., 'OpenMalaria', 'malariasimulation').

    Raises:
        OSError: If there is an issue with executing the command or running the script.
    """

    file_name = f'jobs_{model}_simplerun.ps1'
    file_path = os.path.join(exp.job_directory, file_name)
    write_ps1_runmodel(exp,filename=file_path, model=model)
    cmd_command = f'cmd.exe /c start powershell -ExecutionPolicy Bypass -File "{file_path}"'
    subprocess.Popen(cmd_command, shell=True)


def create_ps1_script(exp, fname, subdir, job_name, py_command):
    """
    This helper function generates a PowerShell script that:
    1. Defines job settings, including job name, working directory, and log directory.
    2. Navigates to the specified subdirectory.
    3. Executes the provided Python command and logs the output to a specified log file.
    4. Pauses the script to keep the console open until the user presses Enter.

    Args:
        exp (object): An experiment object containing the 'job_directory' attribute for saving the script.
        fname (str): The name of the PowerShell script file to be created.
        subdir (str): The subdirectory within the working directory where the Python command should be executed.
        job_name (str): The name of the job, used for log file naming and script content.
        py_command (str): The Python command to be executed within the PowerShell script.

    Raises:
        IOError: If there is an issue with writing the PowerShell script to the file.
    """
    # Construct paths
    file_path = os.path.join(exp.job_directory, fname)
    wdir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

    # Define the content of the PowerShell script
    powershell_content = f"""
# Job settings
$job_name = "{job_name}"
$work_dir = "{wdir}"
$jobdir = "{exp.job_directory}"
$log_dir = Join-Path $jobdir "log"

# Navigate to the subdirectory
Set-Location -Path "$work_dir\\{subdir}"

# Run the Python command
{py_command}`
    >> "$log_dir/run_{job_name}.log" 2>> "$log_dir/run_{job_name}.err"

# Pause to keep the console open
Read-Host "Press Enter to continue"
    """

    # Write the PowerShell script
    with open(file_path, 'w') as file:
        file.write(powershell_content)

    print(f"PowerShell script written to {file_path}")


def write_ps1_analyzer(exp, pyscript, model):
    """
    This function generates a batch file that runs the specified analyzer script for the given model.
    It calls the `create_ps1_script` function to generate the PowerShell script file.

    Args:
        exp (object): An experiment object containing the 'job_directory' attribute for saving the script.
        pyscript (str): The path to the Python script to be run by the analyzer.
        model (str): The model name (e.g., 'OpenMalaria', 'malariasimulation') to customize the script for the specific model.

    Raises:
        ValueError: If the model name or script path is invalid, ensuring correct arguments are passed.
    """
    job_name = f"analyzer_{model}"
    subdir = model
    py_command = f'python {pyscript} --directory "{exp.job_directory}"'
    fname = f'run_analyze_{model}.ps1'
    create_ps1_script(exp, fname, subdir, job_name, py_command)

def submit_run_plotters_local(exp):
    """
    Submits and manages the creation of shell scripts to run standardized plots
    based on the models specified in the experiment.

    Args:
        exp (Experiment): The experiment object that contains attributes such as
            `models` and `plots_to_run`, which determine which models and
            plots should be processed.

    Returns:
        None

    Notes:
        - The function checks which models (EMOD, malariasimulation, OpenMalaria) are
          specified in `exp.models` and sets corresponding job IDs.
        - It prepares a submission script for a set of default plots (`relationship`,
          `timeseries`, `agecurves`) and also handles custom plots if specified in
          `exp.plots_to_run`.
        - If `exp.plots_to_run` is set to `'all'`, all available plots will be processed.
    """
    if not exp.use_container:
        ## Write  submission script for all, even if not running
        for plot_name in exp.plots_to_run:
            pyscript = f"plot_{plot_name}.py"
            job_name = f"run_plot_{plot_name}"
            subdir = "plotter"
            model_args = ' '.join(exp.models)
            py_command = f"python {pyscript} --directory {exp.output_directory} --models {model_args}"

            fname = pyscript.replace('.py', '.ps1')
            create_ps1_script(exp, fname, subdir, job_name, py_command)

        from utility.helper_local  import write_bat_submission_plots
        write_bat_submission_plots(exp)
    else:
        from utility.helper_local_docker  import submit_run_plotters_sh
        submit_run_plotters_sh(exp)

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
    model_args = ' '.join(exp.models)

    # List of plot scripts to run
    plot_scripts = [f'plot_{x}.py' for x in exp.plots_to_run]

    # Start creating the batch script content
    bat_content = f"@echo on\n"
    bat_content += f"set job_name=run_plot_all\n"
    bat_content += f"set work_dir={work_dir}\n"
    bat_content += f"set jobdir={jobdir}\n"
    bat_content += f"set log_dir=%jobdir%\\log\n\n"
    bat_content += f'cd "%work_dir%\\plotter"\n\n'

    # Add commands to run the plotting scripts
    for script in plot_scripts:
        plot_name = script.replace('.py', '')
        bat_content += f'python {script} --directory {exp.output_directory} --models {model_args} >> "%log_dir%\\run_{plot_name}.log" 2>> "%log_dir%\\run_{plot_name}.err"\n'


    # Add pause at the end to keep the terminal open
    bat_content += "pause\n"

    # Write the content to the batch file
    with open(os.path.join(exp.job_directory, filename), 'w') as file:
        file.write(bat_content)

    print(f"Batch script written to {os.path.join(exp.job_directory, filename)}")



