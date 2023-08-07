import argparse, math, os, sys, subprocess, shutil, re, itertools, pickle
from idmtools.entities.experiment import Experiment
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import warnings
import shutil
import os
user = os.getlogin()

def parse_args():
    """
    Parses command-line arguments for simulation specifications.

    Returns:
    argparse.Namespace: Parsed command-line arguments.
    """

    # Set the description for the argument parser
    description = "Simulation specifications"
    parser = argparse.ArgumentParser(description=description)

    # Add the required argument for the job directory
    parser.add_argument(
        "-d",
        "--directory",
        type=str,
        required=True,
        help="Job Directory where exp.obj is located",
    )

    # Parse the command-line arguments and return the result
    return parser.parse_args()
    
def make_dirs(manifest, suite_name, exp_name, custom_subdir=None):
    """
    Creates necessary directories for simulation experiment jobs and simulation outputs.
    Args:
    manifest (Manifest): The manifest object containing project directory information.
    suite_name (str): The name of the suite.
    exp_name (str): The name of the experiment.
    custom_subdir (str): The name of an additional sub-directory (optional) Defaults to None.
    Returns:
    tuple: A tuple containing the job directory path and simulation output directory path.
    """

    # Create the required default paths
    # If custom_subdir is specified, writes directories under given name
    if custom_subdir is not None:
        exp_suite_path = os.path.join(custom_subdir, suite_name)
    else:
        exp_suite_path = os.path.join(suite_name)

    suite_directory = os.path.join(manifest.job_directory, exp_suite_path)  # Grouping folder for simulation exps
    job_directory = os.path.join(manifest.job_directory, exp_suite_path, exp_name)  # stores simulation files to run
    sim_out_dir = os.path.join(manifest.output_directory, exp_suite_path, exp_name)  # stores results csvs and figures

    # Create directories
    os.makedirs(os.path.relpath(job_directory), exist_ok=True)
    os.makedirs(os.path.join(job_directory, 'log'), exist_ok=True)
    os.makedirs(os.path.relpath(sim_out_dir), exist_ok=True)

    # Create subdirectories ('em', 'om', 'comb') inside the simulation output directory if they don't exist
    os.makedirs(os.path.join(sim_out_dir, 'em'), exist_ok=True)
    os.makedirs(os.path.join(sim_out_dir, 'om'), exist_ok=True)
    os.makedirs(os.path.join(sim_out_dir, 'comb'), exist_ok=True)

    # Return the job directory path and simulation output directory path
    return suite_directory, job_directory, sim_out_dir

def check_exp_inputs(exp):
    """
    Helper function to check a list of inputs for validity.
    Args:
        exp (custom class): Custom object that includes all experiment specifications
    """
    if exp.emod_step and exp.num_seeds_burnin >1 & exp.num_seeds_burnin is not exp.num_seeds:
        raise ValueError('num_seeds_burnin needs to be 1 or equal to num_seeds')

def get_emod_time_param(start_year, end_year, burnin, emod_step = None):
    """
    Calculates simulation time parameters for EMOD (OpenMalaria) based on the provided arguments.

    Args:
        start_year (int): Monitoring start year (required by OpenMalaria utils).
        end_year (int): Monitoring and simulation end year (required by OpenMalaria utils).
        burnin (int): Duration of pre-monitoring years to run.
        emod_step (string): Whether EMOD runs in one or two steps ('None' (one run), 'burnin' or 'pickup' (two separate runs)).

    Returns:
        tuple: A tuple containing the simulation start year, number of years to monitor (required in EMOD analyzer),
        and the total simulation duration in years.
        - sim_start_year: Simulation start year
        - monitoring_years: Number of years to monitor (requried in EMOD analyzer)
        - sim_dur_years: Total simulation duration years
    """

    # Calculate the burn-in start year
    burnin_start_year = start_year - burnin

    # Calculate the number of years to monitor
    monitoring_years = end_year - start_year

    if emod_step == None:
        print(" --------| Running EMOD burnin + pickup time in one simulation run |--------")
        sim_dur_years = end_year - burnin_start_year
        sim_start_year = burnin_start_year
    elif emod_step == 'burnin':
        print(" --------| Running EMOD burnin (step 1) |--------")
        sim_dur_years = burnin
        sim_start_year = burnin_start_year
    elif emod_step == 'pickup':
        print(" --------| Running EMOD pickup from serialized burnin (step 2) |--------")
        sim_dur_years = end_year - start_year
        sim_start_year = start_year
    else:
        raise ValueError(f'Please specify valid emod_step, {emod_step} is not valid')
    return sim_start_year, monitoring_years, sim_dur_years


def save_exp_scen(exp, scen_df, save_dirs):
    """
    Saves the experiment and scenario data to the specified save directories.

    Args:
        exp (object): The experiment object to be saved.
        scen_df (pandas.DataFrame): The scenario data to be saved.
        save_dirs (list): List of directories to save the data.

    Returns:
        None
    """
    for sdir in save_dirs:
        # Save the scenario data as a CSV file
        scen_df.to_csv(os.path.join(sdir, 'scenarios.csv'), index=False)

        # Save the experiment object using pickle
        pickle.dump(exp, open(os.path.join(sdir, "exp.obj"), "wb"))


def get_seasonal_eir():
    """
    Generates seasonal EIR (Entomological Inoculation Rate) values.

    Args:
        None (yet)

    Returns:
        tuple: A tuple containing the daily, monthly, seasonal, and perennial EIR values.
        - season_daily: defined seasonal shape
        - season_month: season_daily aggregated to months
        - seasonal: season_month rescaled within 0 to 1
        - perennial: perennial values per month
    """

    # Define the functional form of the non-perennial, seasonal setting
    # season_daily =  1 + np.sin(2 * np.pi * (np.arange(0, 365) / 365))  ## used in EMOD-OM benchmarking
    season_daily = 1 + np.sin(2 * np.pi * (np.arange(0, 365) / 365)) / 2 + np.cos(
        2 * np.pi * (np.arange(0, 365) / 365)) / 2

    season_month = [season_daily[1 + int(i * (365 / 12))] for i in range(0, 12)]

    seasonal = season_month / np.max(season_month)
    # eir_sum = sum(season_month)
    # seasonal = [(x / eir_sum) for x in season_month] # rescale to sum =1
    perennial = [x / 12 for x in [1] * 12]

    return season_daily, season_month, seasonal, perennial


def create_scenarios_csv(exp, col_list=None):
    """
    Creates a scenarios CSV file based on the provided experiment object and column list.

    Args:
        exp (object): The experiment object containing the scenario attributes.
        col_list (list): List of attribute names to include in the scenarios CSV file. Default is None,
        which includes the attributes ['eirs', 'cm_clinical', 'seasonality'].

    Returns:
        pandas.DataFrame: A DataFrame representing the scenarios.

    """

    if col_list is None:
        col_list = ['eirs', 'cm_clinical', 'seasonality']

    # Get the attribute values from the experiment object
    my_attrs = [getattr(exp, attr) for attr in col_list]

    # Generate all combinations of attribute values
    df_array = np.array(list(itertools.product(*my_attrs)))

    # Create a DataFrame with the combinations
    df = pd.DataFrame(df_array)
    df.columns = col_list
    df.reset_index(inplace=True)
    df['index'] = df['index']+1
    return df


def as_list(x):
    """
    Converts the input x to a list if it is not already a list.
    """
    return x if isinstance(x, list) else [x]


def exec(command):
    """
    Executes the specified command in a subprocess.
    Args:
        command (str): The command to execute.
    Returns:
        subprocess.Popen: A Popen object representing the subprocess.
    """
    return subprocess.Popen(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE,
                            universal_newlines=True, text=True)


def shell_header_quest(sh_account, time_str='04:00:00', memG=3, job_name='myjob', arrayJob=None, mem_scl=1):
    # Create 'log' subfolder if it doesn't exist
    if not os.path.exists('log'):
        os.makedirs(os.path.join('log'))

    # If not running on buyin account, need to select partition based on time required
    if not sh_account['buyin']:
        t = datetime.strptime(time_str, '%H:%M:%S').time().hour
        if t < 4:
            sh_account["p"] = 'short'
        if t >= 4:
            sh_account["p"] = 'normal'
        if t >= 12:
            sh_account["p"] = 'long'

    header = f'#!/bin/bash\n' \
             f'#SBATCH -A {sh_account["A"]}\n' \
             f'#SBATCH -p {sh_account["p"]}\n' \
             f'#SBATCH -t {time_str}\n' \
             f'#SBATCH -N 1\n' \
             f'#SBATCH --ntasks-per-node=1\n' \
             f'#SBATCH --mem={int(memG * mem_scl)}G\n' \
             f'#SBATCH --job-name="{job_name}"\n'
    if arrayJob is not None:
        array = arrayJob
        err = '#SBATCH --error=log/slurm_%A_%a.err\n'
        out = '#SBATCH --output=log/slurm_%A_%a.out\n'
        header = header + array + err + out
    else:
        err = f'#SBATCH --error=log/{job_name}.%j.err\n'
        out = f'#SBATCH --output=log/{job_name}.%j.out\n'
        header = header + err + out
    return header


def write_txt(txtobj, path, fname):
    """
    Writes a text object to a file.
    Args:
        txtobj (str): The text object to write.
        path (str): The path to the directory where the file will be saved.
        fname (str): The filename to use for the file.

    """
    file = open(os.path.join(path, fname), 'w')
    file.write(txtobj)
    file.close()


def submit_analyze_OpenMalaria(exp, t='04:00:00', memG=3):
    """
    Submits a job to analyze OpenMalaria simulation results.

    Args:
        exp (object): The experiment object containing job directory information.

    """
    # Generate the SLURM shell script header for the job
    header_post = shell_header_quest(exp.sh_hpc_config, t, memG, job_name=f'analyze_OMsim', mem_scl=exp.mem_increase_factor)

    # Create the Python command to run the analyzer
    if exp.hpc == 'NUCLUSTER':
        pycommand = f'\ncd /home/{user}/model-characterization/OpenMalaria' \
                    f'\npython analyze_sim.py --dir "{exp.job_directory}"'
    elif exp.hpc == 'SCICORE':
        pycommand = f'\ncd /scicore/home/scicore/cavelan/git/model-characterization/OpenMalaria' \
                    f'\n\nml Python/3.9.6-GCCcore-11.2.0-bare' \
                    f'\nsource /scicore/home/scicore/cavelan/git/model-characterization/emodenv/bin/activate' \
                    f'\npython analyze_sim.py --dir "{exp.job_directory}"'
    else:
        raise ValueError('HPC specification not available, must be NUCLUSTER or SCICORE')

    # Write the shell script to a file
    script_path = os.path.join(exp.job_directory, f'run_analyzer_OpenMalaria.sh')
    file = open(script_path, 'w')
    file.write(header_post + pycommand)
    file.close()

    # Read the job ID from the 'job_id.txt' file
    job_id_path = os.path.join(exp.job_directory, 'job_id.txt')
    job_id = open(job_id_path).read().strip()

    # Submit the job with dependency on the previous job
    p = subprocess.run(['sbatch', '--parsable', f'--dependency=afterany:{job_id}', script_path], stdout=subprocess.PIPE,
                       cwd=str(exp.job_directory))

    # Extract the SLURM job ID from the output
    slurm_job_id = p.stdout.decode('utf-8').strip().split(';')[0]

    # Print the submitted job ID and save it to a file
    print(f'Submitted OpenMalaria analyzer - job id: {slurm_job_id}')
    write_txt(slurm_job_id, exp.job_directory, 'job_id_OManalyze.txt')


def submit_analyze_EMOD(experiment, platform, t='04:00:00', memG=3):
    """
    Submits a job to analyze EMOD simulation results.

    Args:
        experiment (object): The experiment object containing job directory and other information.
        platform (object): The platform object representing the HPC platform.

    """

    # Get the current working directory
    wdir = os.path.abspath(os.path.dirname(__file__))

    # Generate the SLURM shell script header for the job
    header_post = shell_header_quest(experiment.sh_hpc_config, t, memG, job_name=f'analyze_EMODsim',
                                     mem_scl=experiment.mem_increase_factor)

    # Get the EMODpy virtual environment path
    emodpy_venv = emodpy_module(experiment.hpc)

    # Generate the Python commands to run additional scripts
    # If any, add  python or R scripts to directly run after analyzer can be added below
    pycommand = '\n'.join(
        [f'\npython {scr} -d {experiment.job_directory} -i {experiment.id}' for scr in experiment.analyzer])

    # Write the shell script to a file
    script_path = os.path.join(experiment.job_directory, f'run_analyzer_EMOD.sh')
    file = open(script_path, 'w')
    file.write(header_post + emodpy_venv + f'\ncd {wdir}/EMOD' + pycommand)
    file.close()

    # Get the job ID
    job_id = platform._op_client.get_job_id(experiment.id, experiment.item_type)[0]

    # Submit the job with dependency on the previous job
    p = subprocess.run(['sbatch', '--parsable', f'--dependency=afterany:{job_id}', script_path], stdout=subprocess.PIPE,
                       cwd=str(experiment.job_directory))

    # Extract the SLURM job ID from the output
    slurm_job_id = p.stdout.decode('utf-8').strip().split(';')[0]

    # Print the submitted job ID
    print(f'Submitted EMOD analyzer - job id: {slurm_job_id}')

    # Write out the job IDs and experiment ID to files
    write_txt(job_id, experiment.job_directory, 'job_id_EMODsim.txt')
    write_txt(experiment.id, experiment.job_directory, 'exp_id_EMODsim.txt')
    write_txt(slurm_job_id, experiment.job_directory, 'job_id_EMODanalyze.txt')


def submit_run_pyscript(exp, pyscript='benchmark_plots.py', shname='run_benchmark_plots.sh',
                        custom_args='--emodom EMOD OpenMalaria', t='01:00:00', memG=1, job_id=None):
    """
    Submits a job to run a Python script.

    Args:
        exp (object): The experiment object containing job directory and other information.
        pyscript (str, optional): The name of the Python script to run. Defaults to 'benchmark_plots.py'.
        shname (str, optional): The name of the shell script to submit. Defaults to 'run_benchmark_plots.sh'.
        job_id (str or None, optional): The job ID to set as dependency. Defaults to None.

    """

    # Get the current working directory
    wdir = os.path.abspath(os.path.dirname(__file__))

    # Generate the SLURM shell script header for the job
    header_post = shell_header_quest(exp.sh_hpc_config, t, memG, job_name=f'pyjob', mem_scl=1)

    # Get the EMODpy virtual environment path
    emodpy_venv = emodpy_module(exp.hpc)

    # Generate the Python command to run the script
    pycommand = f'\npython {pyscript} -d {exp.sim_out_dir} {custom_args}'

    # Write the shell script to a file
    script_path = os.path.join(exp.job_directory, shname)
    file = open(script_path, 'w')
    file.write(header_post + emodpy_venv + f'\ncd {wdir}' + pycommand)
    file.close()

    # Check if job_id is provided as a string
    if isinstance(job_id, str):
        job_id = open(os.path.join(exp.job_directory, F'{job_id}.txt')).read().strip()

        # Submit the job with or without dependency
        p = subprocess.run(['sbatch', '--parsable', f'--dependency=afterany:{job_id}', script_path],
                           stdout=subprocess.PIPE,
                           cwd=str(exp.job_directory))
    else:
        p = subprocess.run(['sbatch', '--parsable', script_path], stdout=subprocess.PIPE, cwd=str(exp.job_directory))

    # Extract the SLURM job ID from the output
    slurm_job_id = p.stdout.decode('utf-8').strip().split(';')[0]

    # Print the submitted job ID
    print(f'Submitted {shname} to run {pyscript} - job id: {slurm_job_id}')


def emodpy_module(location='NUCLUSTER'):
    """
    Returns the EMODpy virtual environment activation command based on the specified location.
    Args:
        location (str, optional): The location identifier. Defaults to 'NUCLUSTER'.
    Returns:
        str: The EMODpy virtual environment activation command.
    """
    if location == 'NUCLUSTER':
        emod_venv = '\n\nml singularity/3.8.1 \nml python/3.8.4' \
                    '\nsource /projects/b1139/environments/emodpy_om/bin/activate\n'
    if location == 'SCICORE':
        emod_venv = '\n\nml Python/3.9.6-GCCcore-11.2.0-bare' \
                    '\nsource /scicore/home/scicore/cavelan/git/model-characterization/emodenv/bin/activate\n'
    return emod_venv


def OM_module(location='NUCLUSTER', om_version=45):
    """
    Returns the OpenMalaria module load command based on the specified location and version.
    Args:
        location (str, optional): The location identifier. Defaults to 'NUCLUSTER'.
        om_version (int, optional): The OpenMalaria version. Defaults to 45.
    Returns:
        str: The OpenMalaria module load command.
    Raises:
        ValueError: If the specified OpenMalaria version is not valid.
    """

    if location == 'NUCLUSTER':
        if om_version == 43:
            ommodule = '\n\nmodule use /projects/b1139/OpenMalaria/modules/ \nmodule load openmalaria\n'
        elif om_version == 45:
            ommodule = '\n\nmodule use /projects/b1139/OpenMalaria/om_v45/modules/ \nmodule load openmalaria\n'
        else:
            raise ValueError(f'{om_version} not a valid OpenMalaria version, available versions: 43, 45')
    if location == 'SCICORE':
        ommodule = '\n\nmodule load OpenMalaria/43.1-iomkl-2019.01\n'
    return ommodule


def combine_emodom_results(sim_out_dir):
    """
    Combines EMOD and OpenMalaria benchmark results into a single DataFrame and saves it as a CSV file.
    Args:
        sim_out_dir (str): The directory containing the simulation output.
    """
    # Read EMOD and OpenMalaria benchmark CSV files
    df_em = pd.read_csv(os.path.join(sim_out_dir, 'em', 'OM_benchmark.csv'))
    df_om = pd.read_csv(os.path.join(sim_out_dir, 'om', 'EMOD_benchmark.csv'))

    # Add 'emodom' column to identify the source of the results
    df_em['emodom'] = 'EMOD'
    df_om['emodom'] = 'OpenMalaria'

    # Append EMOD and OpenMalaria DataFrames
    df = pd.concat(df_em, df_om)

    # Save the combined DataFrame as a CSV file
    df.to_csv((os.path.join(sim_out_dir, 'comb', f'benchmark.csv')), index=False)


def str_to_digit(x):
    """
    Converts a string to a float if possible, otherwise returns the original string.
    Args:
        x (str): The input string.
    Returns:
        float or str: The converted float if conversion is successful, otherwise the original string.
    """
    try:
        x = float(x)
    except:
        x = x
    return x


def pretty_legend(fig, ltitle, r_adj=0.80, round_values=False):
    """
    Adds a legend to a matplotlib figure with prettified labels and title.

    Args:
        fig (matplotlib.figure.Figure): The figure to add the legend to.
        ltitle (str): The title of the legend.
        r_adj (float, optional): The adjustment parameter for the legend's position on the right. Defaults to 0.80.
        round_values (bool, optional): Whether to round the legend labels to two decimal places. Defaults to False.

    Returns:
        matplotlib.figure.Figure: The updated figure with the legend.

    """

    # Get handles and labels from the figure's current axes
    handles, labels = fig.gca().get_legend_handles_labels()

    # Round the labels if required
    if round_values:
        labels = [str_to_digit(x) for x in labels]
        labels = [round(x, 2) for x in labels]

    # Create a dictionary mapping labels to handles
    by_label = dict(zip(labels, handles))

    # Add the legend to the figure
    fig.legend(by_label.values(), by_label.keys(), loc=7, title=ltitle[:20])
    fig.tight_layout()

    # Adjust the position of the legend on the right and return
    return fig.subplots_adjust(right=r_adj)
