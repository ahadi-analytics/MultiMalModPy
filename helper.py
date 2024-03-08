import argparse
import os
import subprocess
import itertools
import pickle
from datetime import datetime
from datetime import datetime as dt
import pandas as pd
import numpy as np
from EMOD.scaffolds.dynamicEIR import eir_to_lhs_regr
from scipy.interpolate import interp1d
from idmtools.entities.experiment import Experiment

def parse_launch_args():
    parser = argparse.ArgumentParser(description="Description of your script.")

    # Define command-line arguments with default values
    parser.add_argument("-d", "--directory",
                        type=str,
                        required=False,
                        help="Jobdirectory of burnin, if no EMOD burnin, is ignored")
    parser.add_argument('--suite',
                        type=str,
                        default=f'test_sims_{dt.now().strftime("%Y%m%d")}',
                        help='Description of SUITEname')
    parser.add_argument('--expname',
                        type=str,
                        default=f'sims_entomologymode_seasonality_intervention_{dt.now().strftime("%H_%M_%S")}',
                        help='Description of exp_name')
    parser.add_argument('--emodstep',
                        type=str,
                        default=None,
                        help='Description of emod_step')
    parser.add_argument('--serializedid',
                        type=str,
                        default='',
                        help='Description of emod_serialized_id')
    parser.add_argument('--models',
                        nargs='+',
                        default=['EMOD', 'OpenMalaria', 'MalSim'],
                        choices=['EMOD', 'OpenMalaria', 'MalSim'],
                        help='Description of models_to_run')
    parser.add_argument('--user',
                        type=str,
                        default=os.environ.get('USER'),
                        help='Subdirectory for simulations by user (or b1139 on NUCLUSTER)')
    parser.add_argument('--no_malsim_burnin',
                        action='store_false',
                        help='MalSim_run_burnin, if no_malsim_burnin specified no burnin is run')
    parser.add_argument('--csv',
                        type=str,
                        required=False,
                        help='Name of scenario csv')
    parser.add_argument('-i', '--interventions',
                        nargs='+',
                        default=[],
                        choices=['cc_step', 'smc'],
                        help='Specify which interventions to run, if any')
    parser.add_argument('--rownum',
                        type=int,
                        required=False,
                        help='Row number of specified scenario csv')
    return parser.parse_args()


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


def get_param_from_dataframe(df, name):
    """
    Retrieves a parameter value from a DataFrame and returns it in the correct format for storage in an experiment object (exp).

    Example:
        exp.seasonality = get_param(exp_scen_df, 'seasonality', listparam=True)

    Args:
        df (pandas.DataFrame): The DataFrame containing the parameter value.
        name (str): The name of the parameter.
        listparam (bool, optional): Indicates whether the parameter value should be returned as a list. Defaults to False.

    Returns:
        Union[list, str]: The parameter value, either as a list or a string, based on the 'listparam' argument.

    """

    # list of parameters expecting list format  # FIXME, better way to do?
    listparams = ['seasonality', 'sweep_list', 'cm_clinical', 'eir', 'intervention_list', 'agebins',
                  'eir_scalar_malsim', 'eir_malsim', 'eir_scalar_om', 'eir_scalar_emod', 'eir_om', 'eir_scalar_om',
                  'carrying_capacity_step']

    value = df[name].iat[0]

    if name in listparams:
        try:
            out = value.replace(' ', '').split(',')
            out = [float(i) if i.isdigit() else i for i in out]  # some might require int?
        except:
            out = [value]
    else:
        out = value

    return out


def initialize_exp(args, manifest):
    exp = Experiment()
    exp.SUITEname = args.suite
    exp.exp_name = args.expname
    exp.emod_step = args.emodstep
    exp.models_to_run = args.models
    exp.MalSim_run_burnin = args.no_malsim_burnin  ## bool on whether to run burnin or not, default if not specified is True
    exp.intervention_list = args.interventions

    # Name and location of simulation, a SUITE may contain multiple experiments that belong to a shared objective
    exp.user = args.user
    exp.custom_subdir = exp.user  # If None, no subdir created

    ## Manifest objects
    exp.hpc = manifest.hpc
    exp.sh_hpc_config = manifest.sh_hpc_config
    exp.selected_platform = manifest.selected_platform
    exp.om_version = manifest.om_version
    exp.emod_build = manifest.emod_build
    exp.om_path = manifest.OM_PATH
    exp.om_input_path = manifest.om_input_path
    exp.job_directory_manifest = manifest.job_directory
    exp.output_directory_manifest = manifest.output_directory

    # Specify OpenMalaria XML and survey step, MalSim simulation setup
    # Note if, interventions are specified in intervention_list, these will get updated via get_intervention_params
    exp.om_scaffold = "R0000GA"  # defining which OpenMalaria XML scaffold to use
    exp.om_survey_step = '30d'
    exp.MalSim_script = 'malsim_benchmarking_exercise.R'
    exp.emod_analyzer = ['analyze_sim.py']
    exp.openmalaria_analyzer = ['analyze_sim.py']

    # Flag to select whether to run with (dynamic) or without vector model (forced)
    exp.entomology_mode = 'dynamic'  # dynamic, forced
    exp.seasonality = [
        'seasonal']  # ["perennial", "seasonal"]  #"Current framework support only 1 seasonality patten per experiment"
    exp.mem_increase_factor = 5.0  # scaling factor on default memory requested

    # Define simulation population and seeds
    exp.pop_size = 10000  # 1000 for testing
    exp.agebins = [0.5, 1, 2, 5, 10, 15, 20, 100]  # Note, keep these to ensure smooth postprocessing
    exp.age_groups_aggregates = [[0, 0.5], [0.5, 1], [1, 2], [2, 5], [5, 10], [10, 15], [15, 20], [20, 100], [0, 5], [0, 100]]

    exp.num_seeds_burnin = 1  # used only if emod_step=='burnin', for EMOD
    exp.num_seeds = 20  # suggested minimum 3, in production 5-10
    exp.start_year = 2000  # start of pickup and monitoring period (for EMOD set given burnin and serialization flags)
    exp.end_year = 2005  # end of pickup and monitoring period
    exp.burnin = 80  # Duration of burnin (pre-monitoring) period, should be 80 years to establish immunity in the population

    # Name of parameters to vary
    exp.sweep_list = ['eir', 'cm_clinical', 'seasonality']
    exp.emod_calib_params = False  # A new function in the framework, are we passing along our within host framework recalibrated parameters, default will be false.
    
    if exp.emod_calib_params:
        exp.calib_config_pointer = range(0, 3)  # define rows from calib_params df to run
        exp.sweep_list = exp.sweep_list + ['calib_config_pointer']

    # Define case management start and coverage
    # 0.2029544 in OpenMalaria corresponds to 5-day probability already converted from 2 weeks coverage, use same for EMOD?
    exp.cm_start = 1
    exp.cm_clinical = [0.0]  # [0, 0.2, 0.4, 0.6, 0.8, 1]  #[0.2029544]
    exp.cm_severe = 0.48  # keep fixed and single value, if < cm_clinical will be updated automatically to cm_clinical * 1.15
    exp.detectionLimit = 40
    exp.eir = [32]

    # Whether to pass along NU's within-host framework recalibrated parameters.
    exp.emod_calib_params = False

    return (exp)


def get_intervention_params(exp):
    from scenario_inputs.intervention_params import exp_params_to_update
    return exp_params_to_update(exp)


def make_dirs(exp, overwrite=False):
    """
    Creates necessary directories for a simulation experiment.

    Args:
    exp (Experiment): The experiment object containing project directory information.
    overwrite (bool, optional): If True, existing directories will be overwritten. Defaults to False.

    Returns:
    exp (Experiment): The experiment object with updated directory paths.
    """

    # Define paths based on experiment parameters
    # If custom_subdir is specified, writes directories under given name
    if exp.custom_subdir is not None:
        exp_suite_path = os.path.join(exp.custom_subdir, exp.SUITEname)
    else:
        exp_suite_path = os.path.join(exp.SUITEname)

    # Define the job directory path and simulation output directory path
    exp.suite_directory = os.path.join(exp.job_directory_manifest,
                                       exp_suite_path)  # Grouping folder for simulation exps
    exp.job_directory = os.path.join(exp.job_directory_manifest, exp_suite_path,
                                     exp.exp_name)  # stores simulation files to run
    exp.sim_out_dir = os.path.join(exp.output_directory_manifest, exp_suite_path,
                                   exp.exp_name)  # stores results csvs and figures

    # Create directories
    os.makedirs(exp.job_directory, exist_ok=overwrite)
    os.makedirs(os.path.join(exp.job_directory, 'log'), exist_ok=overwrite)
    os.makedirs(exp.sim_out_dir, exist_ok=overwrite)

    # Create subdirectories for specific simulation models included in exp.models_to_run
    if 'EMOD' in exp.models_to_run:
        os.makedirs(os.path.join(exp.sim_out_dir, 'em'), exist_ok=overwrite)

    if exp.emod_step != 'burnin':
        if 'OpenMalaria' in exp.models_to_run:
            os.makedirs(os.path.join(exp.sim_out_dir, 'om'), exist_ok=overwrite)
        if 'MalSim' in exp.models_to_run:
            os.makedirs(os.path.join(exp.sim_out_dir, 'MalSim'), exist_ok=overwrite)
    return exp


def check_exp_inputs(exp):
    """
    Helper function to validate experiment inputs.

    Args:
        exp (Experiment): Custom object containing experiment specifications.

    Raises:
        ValueError: If input parameters are invalid.
    """

    if exp.emod_step:
        if exp.num_seeds_burnin != 1:
            raise ValueError('Current framework only allows 1 seed for EMOD burnin')

        # Obsolete if num_seeds_burnin requires to be 1, as if 1, multiple num_seeds are allowed
        # if exp.num_seeds_burnin != 1 and exp.num_seeds_burnin != exp.num_seeds:
        #    raise ValueError('num_seeds_burnin must be 1 or equal to num_seeds')

    if len(exp.seasonality) > 1:
        raise ValueError(f'Only one seasonality pattern is allowed, but {len(exp.seasonality)} specified.')

    if exp.burnin < 80 and (('EMOD' in exp.models_to_run and exp.emod_step != 'pickup') or
                            'EMOD' not in exp.models_to_run):
        print(f'WARNING: Short burnin period of {exp.burnin} years. A burnin of at least 80 years is recommended.')

    if np.max(exp.cm_clinical) > 0 and exp.entomology_mode == 'dynamic' and 'EMOD' in exp.models_to_run:
        raise ValueError('EMOD is not set up to run dynamic EIR for non-zero CM-levels currently.')

    # Check if any attribute in list_attributes_nGT1 is not in sweep_list
    attributes_dict = exp.__dict__
    list_attributes_nGT1 = list()

    # Check if any attribute in list_attributes_nGT1 is not in sweep_list
    attributes_dict = exp.__dict__
    list_attributes_nGT1 = list()

    for key, value in attributes_dict.items():
        # Check if the attribute is a list
        if isinstance(value, list) and len(value) > 1:
            if key not in ['models_to_run', 'eir_scalar_emod', 'eir_malsim', 'eir_scalar_malsim', 'eir_om', 'eir_scalar_om', 'carrying_capacity_step',
                           'agebins', 'sweep_list', 'season_daily', 'season_month', 'seasonal', 'perennial']:
                list_attributes_nGT1.append(key)

    list_attr_notsweep = [attr for attr in list_attributes_nGT1 if attr not in attributes_dict['sweep_list']]
    if list_attr_notsweep:
        raise ValueError(
            f'The following attributes have more than 1 value but are not included in sweep_list: {", ".join(list_attr_notsweep)}')


def get_simulation_time_params(exp):
    """
    Calculates simulation time parameters for EMOD, OpenMalaria and malariasimulation based on the provided arguments.

    Args:
        exp (Experiment): Experiment object containing experiment specifications.
            - start_year (int): Monitoring start year (required by OpenMalaria utils).
            - end_year (int): Monitoring and simulation end year (required by OpenMalaria utils).
            - burnin (int): Duration of pre-monitoring years to run.
            - emod_step (str): Whether EMOD runs in one or two steps ('None' (one run), 'burnin', or 'pickup' (two separate runs)).

    Returns:
        exp (Experiment): Experiment object with updated simulation time parameters.
            - sim_start_year: Simulation start year
            - monitoring_years: Number of years to monitor (requried in EMOD analyzer)
            - sim_dur_years: Total simulation duration years
    """

    start_year = exp.start_year
    burnin = exp.burnin
    end_year = exp.end_year
    models_to_run = exp.models_to_run
    emod_step = exp.emod_step

    # Calculate the burn-in start year (per default set to be not monitored)
    burnin_start_year = start_year - burnin

    # Calculate the number of years to monitor
    monitoring_years = end_year - start_year

    if emod_step is None:
        if 'EMOD' in models_to_run:
            print(" --------| Running EMOD burnin + pickup time in one simulation run |--------")
        sim_dur_years = end_year - burnin_start_year
        sim_start_year = burnin_start_year
    elif emod_step == 'burnin':
        if 'EMOD' in models_to_run:
            print(" --------| Running EMOD burnin (step 1) |--------")
        sim_dur_years = burnin
        sim_start_year = burnin_start_year
    elif emod_step == 'pickup':
        if 'EMOD' in models_to_run:
            print(" --------| Running EMOD pickup from serialized burnin (step 2) |--------")
        sim_dur_years = end_year - start_year
        sim_start_year = start_year
    else:
        raise ValueError(f'Please specify valid emod_step, {emod_step} is not valid')

    # Update experiment object with simulation start year and duration
    exp.sim_start_year_em = sim_start_year
    exp.sim_start_year_om = start_year - burnin
    exp.sim_start_year_ms = exp.sim_start_year_om
    if not exp.MalSim_run_burnin:
        exp.sim_start_year_ms = exp.start_year
    exp.monitoring_years = monitoring_years
    exp.sim_dur_years = sim_dur_years

    return exp


def save_scen(scen_df, fname, save_dirs=None):
    """
    Saves a scenario DataFrame to a CSV file in the specified directories.
    Args:
        scen_df (pandas.DataFrame): The DataFrame containing the scenario data.
        fname (str): The name of the CSV file to be saved.
        save_dirs (list of str, optional): List of directories to save the CSV file. Defaults to None.
    """
    for sdir in save_dirs:
        scen_df.to_csv(os.path.join(sdir, fname), index=False)


def save_exp_scen(exp, scen_df, save_dirs):
    """
    Saves the experiment and scenario data to the specified save directories.
    Args:
        exp (Experiment): Experiment object containing experiment specifications.
        scen_df (pandas.DataFrame): The scenario data to be saved.
        save_dirs (list): List of directories to save the data.
    """
    for sdir in save_dirs:
        # Save the scenario data as a CSV file
        scen_df.to_csv(os.path.join(sdir, 'scenarios.csv'), index=False)

        # Save the experiment object using pickle
        pickle.dump(exp, open(os.path.join(sdir, "exp.obj"), "wb"))


def get_seasonal_eir(exp=None):
    """
    Generates seasonal EIR (Entomological Inoculation Rate) values.

    Examples:
        season_daily, season_month, seasonal, perennial = get_seasonal_eir()
        exp = get_seasonal_eir(exp)

    Args:
        exp (Experiment, optional): Experiment object containing experiment specifications.

    Returns:
        tuple or Experiment: A tuple containing the daily, monthly, seasonal, and perennial EIR values if exp is None.
        If exp is provided, the Experiment object with updated seasonal EIR attributes is returned.

        If exp is None:
        - season_daily (list): Defined seasonal shape of daily EIR values.
        - season_month (list): Monthly EIR values calculated from the seasonal pattern.
        - seasonal (list): Seasonal EIR values rescaled within 0 to 1.
        - perennial (list): Perennial EIR values per month.

        If exp is provided:
        -  exp (Experiment): Experiment object with updated seasonality attributes.
    """

    # Define the seasonal setting
    # season_daily =  1 + np.sin(2 * np.pi * (np.arange(0, 365) / 365))  ## functional form used in EMOD-OM benchmarking
    season_month = [56.40649336, 37.27189056, 37.52493552, 36.99289173, 36.58402723, 33.48317104, 33.38009291,
                    33.906819, 37.87905792, 43.51349906, 60.33004287, 62.49708256]
    season_daily = monthly_to_daily_EIR(season_month)
    seasonal = [0.110650869, 0.073115112, 0.073611502, 0.072567808, 0.071765752, 0.065682898, 0.065480693, 0.066513955,
                0.074306173, 0.085359082, 0.118347574, 0.122598589]

    # eir_sum = sum(season_month)
    # seasonal = [(x / eir_sum) for x in season_month] # rescale to sum =1
    perennial = [x / 12 for x in [1] * 12]

    if exp is not None:
        exp.season_daily = season_daily
        exp.season_month = season_month
        exp.seasonal = seasonal
        exp.perennial = perennial
        return exp
    else:
        return season_daily, season_month, seasonal, perennial


def monthly_to_daily_EIR(monthly_EIR):
    """
    Convert monthly EIR values to daily using cubic spline interpolation.

    Args:
        monthly_EIR (list of floats): List of monthly EIRs.

    Returns:
        list of floats: List of daily EIRs.
    """

    if len(monthly_EIR) == 12:
        monthly_EIR.append((monthly_EIR[0] + monthly_EIR[-1]) / 2)
    elif len(monthly_EIR) != 13:
        raise Exception('Monthly EIR should have 12 or 13 values')
    x_monthly = np.linspace(0, 364, num=13, endpoint=True)
    x_daily = np.linspace(0, 364, num=365, endpoint=True)
    EIR = interp1d(x_monthly, monthly_EIR, kind='cubic')
    daily_EIR = EIR(x_daily)
    daily_EIR /= 30
    daily_EIR = daily_EIR.tolist()
    daily_EIR = [max(x, 0) for x in daily_EIR]

    return daily_EIR


def rep_scen_df(df):
    """
    Repeats scenario data in a DataFrame based on the number of seeds.

    Args:
        df (pandas.DataFrame): The DataFrame containing the scenario data.

    Returns:
        pandas.DataFrame: A DataFrame with repeated scenario data based on the number of seeds.
    """

    try:
        df = df.drop(['index'], axis=1)
    except:
        pass
    rep_df = pd.DataFrame(np.repeat(df.to_numpy(), df.num_seeds[0], axis=0), columns=df.columns)
    rep_df.reset_index(inplace=True)
    rep_df['index'] = rep_df['index'] + 1
    rep_df['seed'] = rep_df.groupby('scen_id').cumcount() + 1
    return rep_df


def create_simsetup_csv(exp):
    """
    Creates a CSV file containing simulation setup parameters.
    Args:
        exp (Experiment): Experiment object containing experiment specifications.
    """

    # If other parameters should be savedm these need to be added to setup_dic
    setup_dic = {'job_directory': exp.job_directory,
                 'sim_out_dir': exp.sim_out_dir,
                 'nexps': exp.nexps,
                 'sweep_list': exp.sweep_list,
                 'monitoring_years': exp.monitoring_years,
                 'pop_size': exp.pop_size,
                 'agebins': exp.agebins,
                 'seasonality': exp.seasonality[0],
                 'seasonal': ';'.join(map(str, exp.seasonal)),
                 'perennial': ';'.join(map(str, exp.perennial)),
                 'start_year': exp.start_year,
                 'end_year': exp.end_year,
                 'burnin': exp.burnin,
                 'sim_start_year_om': exp.sim_start_year_om,
                 'sim_start_year_em': exp.sim_start_year_em,
                 'sim_start_year_ms': exp.sim_start_year_ms,
                 'intervention_list': exp.intervention_list
                 }

    setup_df = pd.DataFrame.from_dict(setup_dic, orient='index', columns=['Value'])
    setup_df['parameter'] = setup_df.index
    save_dirs = [exp.job_directory, exp.sim_out_dir]
    for sdir in save_dirs:
        setup_df.to_csv(os.path.join(sdir, 'exp_setup_df.csv'), index=False)


def create_scenarios_csv(exp, col_list, add_cols=True):
    """
    Creates a scenarios CSV file based on the provided experiment object and column list.

    Args:
        exp (Experiment): The experiment object containing the scenario attributes.
        col_list (list): List of attribute names to include in the scenarios CSV file.
            Example: ['eirs', 'cm_clinical', 'seasonality'].
        add_cols (bool, optional): Whether to add additional columns such as 'entomology_mode',
            'num_seeds', etc. Default is True.

    Returns:
        pandas.DataFrame: A DataFrame representing the scenarios.
    """

    if col_list is None:
        col_list = ['eir', 'cm_clinical', 'seasonality']

    # Get the attribute values from the experiment object
    my_attrs = [getattr(exp, attr) for attr in col_list]

    # Generate all combinations of attribute values
    df_array = np.array(list(itertools.product(*my_attrs)))

    # Create a DataFrame with the combinations
    df = pd.DataFrame(df_array)
    df.columns = col_list
    df.reset_index(inplace=True)
    df['index'] = df['index'] + 1
    df['scen_id'] = df['index']

    if add_cols:
        df['entomology_mode'] = exp.entomology_mode
        df['num_seeds'] = exp.num_seeds
        df['cm_start'] = exp.cm_start
        df['cm_clinical'] = pd.to_numeric(df['cm_clinical'], errors='coerce')

        # Parameters requiring adjustment:
        df['cm_severe'] = np.where(df['cm_clinical'] * 1.15 > exp.cm_severe,
                                   np.minimum(df['cm_clinical'] * 1.15, 1), exp.cm_severe)
        df['cm_severe'] = np.where(df['cm_clinical'] == 0, 0, df['cm_severe'])
        if 'cc_step' in exp.intervention_list:
            df['eir_malsim'] = exp.eir_malsim
            df['eir_om'] = exp.eir_om
            df['eir_scalar_timestep_5day'] = exp.eir_scalar_timestep_5day
            df['eir_scalar_timestep_daily'] = exp.eir_scalar_timestep_daily
            df['eir_scalar_emod'] = exp.eir_scalar_emod
            df['eir_scalar_om'] = exp.eir_scalar_om
            df['eir_scalar_malsim'] = exp.eir_scalar_malsim
            df['carrying_capacity_step'] = exp.carrying_capacity_step
        if exp.entomology_mode == 'dynamic':
            df['x_Temporary_Larval_Habitat'] = eir_to_lhs_regr(df, population=exp.pop_size)
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


def shell_header_quest(sh_account, time_str='6:00:00', memG=3, job_name='myjob', arrayJob=None, mem_scl=1):
    """
    Generates the SLURM shell script header for submitting jobs to a high-performance computing cluster.

    Args:
        sh_account (dict): Dictionary containing account information for SLURM.
        time_str (str, optional): Time limit for the job in the format 'HH:MM:SS'. Defaults to '04:00:00'.
        memG (int, optional): Memory required for the job in gigabytes. Defaults to 3.
        job_name (str, optional): Name of the job. Defaults to 'myjob'.
        arrayJob (str, optional): Specification for array jobs. Defaults to None.
        mem_scl (float, optional): Memory scaling factor. Defaults to 1.

    Returns:
        str: The SLURM shell script header.
    """

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
             f'#SBATCH --mem-per-cpu={int(memG * mem_scl)}G\n' \
             f'#SBATCH --job-name="{job_name}"\n'
    if arrayJob is not None:
        array = arrayJob
        err = f'#SBATCH --error=log/{job_name}_%A_%a.err\n'
        out = f'#SBATCH --output=log/{job_name}_%A_%a.out\n'
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



def submit_run_pyscript(exp, pyscript='benchmark_plots.py', shname='run_benchmark_plots.sh',
                        custom_args='--emodom EMOD OpenMalaria MalSim', t='05:00:00', memG=20, job_id_EMOD=None,
                        job_id_MalSim=None,
                        job='pyjob'):
    """
    Submits a job to run a Python script.

    Args:
        exp (Experiment): The experiment object containing job directory and other information.
        pyscript (str, optional): The name of the Python script to run. Defaults to 'benchmark_plots.py'.
        shname (str, optional): The name of the shell script to submit. Defaults to 'run_benchmark_plots.sh'.
        custom_args (str, optional): Custom arguments to pass to the Python script. Defaults to '--emodom EMOD OpenMalaria MalSim'.
        t (str, optional): Wall time for the job in the format 'HH:MM:SS'. Defaults to '01:00:00'.
        memG (int, optional): Memory required for the job in GB. Defaults to 1.
        job_id_EMOD (str or None, optional): The job ID to set as dependency for EMOD. Defaults to None.
        job_id_MalSim (str or None, optional): The job ID to set as dependency for MalSim. Defaults to None.
        job (str, optional): Name of the job. Defaults to 'pyjob'.
    """

    # Get the current working directory
    wdir = os.path.abspath(os.path.dirname(__file__))

    # Generate the SLURM shell script header for the job
    header_post = shell_header_quest(exp.sh_hpc_config, t, memG, job_name=job, mem_scl=1)

    # Get the EMODpy virtual environment path
    emodpy_venv = emodpy_module(exp.hpc)

    # Generate the Python command to run the script
    pycommand = f'\npython {pyscript} -d {exp.sim_out_dir} {custom_args}'

    # Write the shell script to a file
    script_path = os.path.join(exp.job_directory, shname)
    file = open(script_path, 'w')
    file.write(header_post + emodpy_venv + f'\ncd {wdir}' + pycommand)
    file.close()

    # Check if job_id is provided as a string to define dependendies
    if isinstance(job_id_EMOD, str):
        job_id_EMOD = open(os.path.join(exp.job_directory, f'{job_id_EMOD}.txt')).read().strip()

        # Check if job_id_MalSim is provided as a string
        if isinstance(job_id_MalSim, str):
            job_id_MalSim = open(os.path.join(exp.job_directory, f'{job_id_MalSim}.txt')).read().strip()
            dependencies = f'--dependency=afterany:{job_id_EMOD},{job_id_MalSim}'
        else:
            dependencies = f'--dependency=afterany:{job_id_EMOD}'
        # Submit job with dependency
        p = subprocess.run(['sbatch', '--parsable', dependencies, script_path], stdout=subprocess.PIPE,
                           cwd=str(exp.job_directory))
    else:
        # Submit job without dependency
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
