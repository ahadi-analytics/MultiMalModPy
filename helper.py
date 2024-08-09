import argparse
import os
import subprocess
import itertools
import pickle
from datetime import datetime
from datetime import datetime as dt
import pandas as pd
import numpy as np
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
                        choices=[None, 'burnin', 'pickup', 'new_pickup'],
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
    parser.add_argument('--csv',
                        type=str,
                        required=False,
                        help='Name of scenario csv')
    parser.add_argument('-i', '--interventions',
                        nargs='+',  # FIXME how to handle combinations if those should even be allowed
                        default=[],
                        choices=['cc_step', 'smc'],
                        help='Specify which interventions to run, if any')
    parser.add_argument('--rownum',
                        type=int,
                        required=False,
                        help='Row number of specified scenario csv')
    parser.add_argument('--test',
                        action='store_true',
                        help='Specify whether to run a test, population and burnin and seeds will be only a few per default')
    parser.add_argument('--calib',
                        action='store_true',
                        help='Specify whether to run include calibration parameters as a sweep variable')
    parser.add_argument('--overwrite',
                        action='store_true',
                        help='Whether to overwrite simulation experiment folders')
    parser.add_argument('--mpv',
                        default=True,
                        type=bool,
                        help='Specify whether to run malariasimulation with parameter variation, default is to run parameter variation')
    parser.add_argument('--output_type',
                        type=str,
                        default='prevalence_2to10',
                        choices=['prevalence_2to10','eir'], # clinical_incidenceU5 #
                        help='Specify whether to align transmission in each model by EIR or by prevalence_2to10') # , or by clinical incidence
    parser.add_argument('--calibrun',
                        action='store_true',
                        help = "This will run sims to generate interpolaiton data, under given simulation settings.")
    parser.add_argument('--importation',
                        action='store_true',
                        help = "Include Importation in OpenMalaria/EMOD")
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
    """
    Generates the default simulation settings we are interested in using across all three models,
    before any interventions or other functions overwrite the items in exp.
    User, if you want to make adjustments to your simulation and you are not using the overwrite functions,
    I would recommend you make those changes here.

    Example:
        exp.seasonality = get_param(exp_scen_df, 'seasonality', listparam=True)

    Args:
        args (obj, lst): List of inputs grabbed from the parse_args function.
        manifest (file, lst): List of inputs grabbed from the manifest.py file.
            manifest's inputs are more relevant for directories and hpc settings, then simulation settings.
    Returns:
        exp (Experiment): Returns an Experiment Object with simulation and hpc settings that will get shared across 
            the three models.
    """
    exp = Experiment()
    exp.SUITEname = args.suite
    exp.exp_name = args.expname
    exp.emod_step = args.emodstep
    exp.models_to_run = args.models
    exp.intervention_list = args.interventions
    exp.testrun = args.test
    exp.calibrun = args.calibrun
    exp.importation = args.importation
    exp.overwrite = args.overwrite
    exp.overwrite_param = False  # to discuss how we want to handle parameter changes and overwrites in helper vs launch_test.py, or have another flag to add for args
    exp.emod_calib_params = args.calib  # A new function in the framework, are we passing along our within host framework recalibrated parameters, default will be false.
    exp.malariasimulation_parameter_variation = args.mpv

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
    exp.emod_input_path = manifest.emod_input_path
    exp.om_input_path = manifest.om_input_path
    exp.ms_input_path = manifest.ms_input_path
    exp.job_directory_manifest = manifest.job_directory
    exp.output_directory_manifest = manifest.output_directory
    exp.interp_path = manifest.interp_path
    exp.interp_csv = manifest.interp_csv
    exp.burnin_directory = None

    # Specify OpenMalaria XML and survey step, MalSim simulation setup
    # Note if, interventions are specified in intervention_list, these will get updated via get_intervention_params
    exp.om_scaffold = "R0000GA"  # defining which OpenMalaria XML scaffold to use
    exp.om_survey_step = '5d'  # '30d'
    exp.MalSim_script = 'malsim_benchmarking_exercise.R'
    exp.analyzer_script = ['analyze_sim.py']
    exp.analyzer_list = ['all_age_analyzer', 'annual', '5day', 'monthly',
                         'benchmark']  # ['all_age_analyzer', '5day', 'annual','monthly','benchmark'.'daily']
    exp.plots_to_run = ['benchmark', 'timeseries',
                        'agecurves']  # gets overwritten by get_intervention_params(exp) depending on 'interventions' specified

    # Flag to select whether to run with (dynamic) or without vector model (forced)
    exp.entomology_mode = 'dynamic'  # dynamic, forced
    exp.seasonality = ['perennial']  # ["perennial", "seasonal"]  
    #"Current framework support only 1 seasonality patten per experiment"
    exp.mem_increase_factor = 5.0  # scaling factor on default memory requested

    # Define age groups to report/monitor in simulations and to aggregate in output
    exp.agebins = [0.5, 1, 2, 5, 10, 15, 20, 100]  # Note, keep these to ensure smooth postprocessing
    exp.age_groups_aggregates = [[0, 0.5], [0.5, 1], [1, 2], [2, 5], [5, 10], [10, 15], [15, 20], [20, 100], [0, 5],
                                 [0, 100]]

    # Define case management start and coverage
    # 0.2029544 in OpenMalaria corresponds to 5-day probability already converted from 2 weeks coverage, use same for EMOD?
    exp.cm_start = 1
    exp.cm_clinical = [0, 0.45]  # [0, 0.2, 0.4, 0.6, 0.8, 1]  #[0.2029544]
    exp.cm_severe = 0.48  # keep fixed and single value, if < cm_clinical will be updated automatically to cm_clinical * 1.15
    exp.detectionLimit = 40

    if exp.calibrun:
        if args.output_type != 'eir':
            print("Warning: For Calibrun Simulations, output_type will equal eir")
        exp.output_type = 'eir'
        exp.analyzer_list = ['benchmark']
        exp.plots_to_run = ['benchmark']
    else:
        exp.output_type = args.output_type
    if exp.output_type == 'eir':
        exp.output_target = [1, 5, 10, 20, 50, 100, 500, 1000]
        # exp.output_target = [0.25, 0.5, 0.75, 0.9, 1, 1.1, 1.25, 1.5, 1.75,2, 
        #                      2.5, 2.75, 3, 3.25, 4, 5, 6, 7, 8, 9,
        #                      10, 12, 14, 16, 18, 20, 25, 30, 35, 40,
        #                      45, 50, 100, 200, 500, 1000]           
    elif exp.output_type == 'prevalence_2to10':
        exp.output_target = [0.05,0.1,0.2,0.25,0.4,0.45,0.5,0.6,0.7,0.8]
    else:
        print("Warning: we do not offer input types that aren't pfpr or eir")
    # Define simulation population and seeds
    if exp.testrun:
        exp.pop_size = 1000
        exp.num_seeds_burnin = 1
        exp.num_seeds = 1
        exp.start_year = 2000
        exp.end_year = 2005
        exp.burnin = 10
        if exp.output_type == 'eir':
            exp.output_target = [1,5,10,20,35,50]
        elif exp.output_type == 'prevalence_2to10':
            exp.output_target = [0.05,0.1,0.25,0.4,0.5,0.6]
        else:
            print("Warning: we do not offer input types that aren't pfpr or eir")
        #if exp.hpc == 'NUCLUSTER':
        #    exp.sh_hpc_config['p'] = 'b1139testnode'  # Use test allocation
    else:
        exp.pop_size = 10000
        exp.num_seeds_burnin = 1  # used only if emod_step=='burnin', for EMOD
        exp.num_seeds = 20  # suggested minimum 3, in production 5-10
        exp.start_year = 2000  # start of pickup and monitoring period (for EMOD set given burnin and serialization flags)
        exp.end_year = 2005  # end of pickup and monitoring period
        exp.burnin = 80  # Duration of burnin (pre-monitoring) period, should be 80 years to establish immunity in the population

    # Name of parameters to vary
    exp.sweep_list = ['output_target', 'cm_clinical', 'seasonality']
    if exp.emod_calib_params:
        calib_config_df = pd.read_csv(os.path.join(exp.emod_input_path, 'emod_best.csv'))
        exp.calib_config_pointer = range(0, len(calib_config_df))  # define rows from calib_params df to run
        del calib_config_df
        exp.sweep_list = exp.sweep_list + ['calib_config_pointer']

    return (exp)


def output_target_to_xTemp(df, exp,  model):
    interp_path = os.path.join(exp.interp_path, model, exp.interp_csv)
    if not os.path.exists(interp_path):
        raise ValueError(f'interp_file not found: {interp_path}')

    data = pd.read_csv(interp_path)
    output = []

    if exp.output_type == 'eir':
        output_type_col = 'simulatedEIR'
    elif exp.output_type == 'prevalence_2to10':
        output_type_col = 'prevalence_2to10'
    elif exp.output_type == 'clinical_incidenceU5':  ## FIXME tbd later on how to add
        output_type_col = 'clinical_cases'  # name including age group?
    else:
        raise ValueError(f'Specified input_type is not valid {exp.output_type}')

    for i, row in df.iterrows():

        idata = data[((data['cm_clinical'] == row['cm_clinical'])
                      & (data['seasonality'] == row['seasonality'])
                      & (data['modelname'] == model))]
        xt = idata[output_type_col]
        yp = idata['input_target']
        xnew = row['output_target']
        interpolated_value = np.interp(xnew, xt, yp)
        pop_fitting_was_run = 10000
        interpolated_value = interpolated_value / (pop_fitting_was_run / exp.pop_size)

        if interpolated_value <= 0:
            interpolated_value = 0.01
            print(
                "Warning: EMOD's x_Temporary_Larval_Habitat < 0, value set to 0.01 (this will likely cause elimination in the simulations)")
        if interpolated_value >= 10000:
            interpolated_value = 9999
            print(
                "Warning: EMOD's x_Temporary_Larval_Habitat > 10000, value set to 9999 (higher values cannot be reasonably simulated)")
        output.append(interpolated_value)
    return output


def output_target_to_eir(df, exp, model):
    interp_path = os.path.join(exp.interp_path, model, exp.interp_csv)
    if not os.path.exists(interp_path):
        raise ValueError(f'interp_file not found: {interp_path}')

    data = pd.read_csv(interp_path)
    output = []
    if exp.output_type == 'eir':
        output_type_col = 'simulatedEIR'
        return df['output_target']
    elif exp.output_type == 'prevalence_2to10':
        output_type_col = 'prevalence_2to10'
    elif exp.output_type == 'clinical_incidenceU5':  ## FIXME tbd later on how to add
        output_type_col = 'clinical_cases'  # name including age group?
    else:
        raise ValueError(f'Specified input_type is not valid {exp.output_type}')

    for i, row in df.iterrows():

        idata = data[((data['cm_clinical'] == row['cm_clinical'])
                      & (data['seasonality'] == row['seasonality'])
                      & (data['modelname'] == model))]
        xt = idata[output_type_col]
        yp = idata['input_target']
        xnew = row['output_target']
        interpolated_value = np.interp(xnew, xt, yp)

        if interpolated_value <= 0:
            interpolated_value = 0.01
            print("Warning: eir < 0, value set to 0.01 (this will likely cause elimination in the simulations)")
        if interpolated_value >= 1000:
            interpolated_value = 999
            print("Warning:  eir > 1000, value set to 999 (higher values cannot be reasonably simulated)")
        output.append(interpolated_value)
    return output


def get_intervention_params(exp):
    """
    Retrieve intervention parameters for a specific experiment.

    Parameters:
    - exp: Experiment object.

    Returns:
    Intervention parameters based on the specified experiment.
    """
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


def exp_obj_to_csv(file_path):
    # Load the pickle object
    with open(os.path.join(file_path, 'exp.obj'), 'rb') as pickle_file:
        data = pickle.load(pickle_file)

    with open(os.path.join(file_path, 'exp_obj.csv'), 'w') as csv_file:
        if isinstance(data, dict):
            # Write the header
            csv_file.write('Key,Value\n')
            # Write the data
            for key, value in data.items():
                csv_file.write(f'{key},{value}\n')
        elif isinstance(data, list):
            # Write the data (assuming it's a list of lists or list of tuples)
            for item in data:
                row = ','.join(map(str, item))
                csv_file.write(f'{row}\n')
        else:
            raise ValueError(
                "The pickle file contains unsupported data type. Only dictionaries and lists are supported.")


def check_exp_inputs(exp):
    """
    Helper function to validate experiment inputs.

    Args:
        exp (Experiment): Custom object containing experiment specifications.

    Raises:
        ValueError: If input parameters are invalid.
    """

    if exp.om_survey_step == '30d' and "5day" in exp.analyzer_list:
        raise Warning('OpenMalaria runs with 30d survey steps , 5day analyzer will cause an error in postprocessing')

    if exp.om_survey_step == '30d' and "cc_step" in exp.intervention_list:
        raise ValueError('cc_step interventions requires 5d survey steps in OpenMalaria')

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

    for key, value in attributes_dict.items():
        # Check if the attribute is a list
        if isinstance(value, list) and len(value) > 1:
            if key not in ['models_to_run', 'eir_scalar_emod', 'eir_malsim', 'eir_scalar_malsim', 'eir_om',
                           'eir_scalar_om', 'carrying_capacity_step', 'age_groups_aggregates', 'plots_to_run',
                           'agebins', 'sweep_list', 'season_daily', 'season_month', 'seasonal', 'perennial',
                           'analyzer_list', 'analyzer_script', 'calib_config_pointer', 'importation',
                           'models_to_run_pickup']:
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


def param_variation(df, exp):
    """
    Perform parameter variation for malariasimulation simulations.

    Parameters:
    - df: DataFrame containing data from scenarios.csv.
    - exp: Experiment object.

    Returns:
    DataFrame with added column 'ms_pv' representing malsim parameter variation values.
    """
    if exp.malariasimulation_parameter_variation:
        from random import sample
        if exp.num_seeds > 1000:
            print("Warning: num_seeds > 1000, therefore malsim parameter variation will have repeat values")
            par_var = [(i % 1000) + 1 for i in sample(range(1, exp.num_seeds + 1), exp.num_seeds)]
            for i, row in df.iterrows():
                df.loc[i, 'ms_pv'] = int(par_var[df.loc[i, 'seed'] - 1])
        else:
            par_var = sample(range(1, 1001), exp.num_seeds)
            for i, row in df.iterrows():
                df.loc[i, 'ms_pv'] = int(par_var[df.loc[i, 'seed'] - 1])
    return df


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
    # Seasonal Profile is based off of EMOD CM = 0, seasonal setting, EIR = 20
    season_month = [2.969670822, 1.841811729, 1.327101791, 0.857686237, 0.611351676, 0.48901135,
                    0.480399615, 0.725799099, 1.140032967, 2.215493305, 3.229497298, 3.844139468]

    season_daily = monthly_to_daily_EIR(season_month)

    eir_sum = sum(season_month)
    seasonal = [(x / eir_sum) for x in season_month] # rescale to sum =1
    perennial = [x / 12 for x in [1] * 12]
    perennial_daily = [x/365 for x in [1]*365]

    if exp is not None:
        exp.season_daily = season_daily
        exp.season_month = season_month
        exp.seasonal = seasonal
        exp.perennial = perennial
        exp.perennial_daily = perennial_daily
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
                 'emod_serialized_id': exp.emod_serialized_id,
                 'burnin_directory': exp.burnin_directory,
                 'nexps': exp.nexps,
                 'sweep_list': exp.sweep_list,
                 'monitoring_years': exp.monitoring_years,
                 'pop_size': exp.pop_size,
                 'agebins': exp.agebins,
                 'seasonality': exp.seasonality[0],
                 'seasonal_monthly': ';'.join(map(str, exp.seasonal)),
                 'perennial_monthly': ';'.join(map(str, exp.perennial)),
                 'seasonal_daily': ';'.join(map(str, exp.season_daily)),
                 'perennial_daily': ';'.join(map(str, exp.perennial_daily)),
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
        col_list = ['output_target', 'cm_clinical', 'seasonality']

    if exp.calibrun:
        if not exp.importation:
            print("Notice: for calibrun simulations, importation will be set to True")
            exp.importation = True
        exp.output_target = np.arange(1,31)
        eir_range = [1.00000000e-01, 1.37382380e-01, 1.88739182e-01, 2.59294380e-01, 3.56224789e-01, 4.89390092e-01,
                    6.72335754e-01, 9.23670857e-01, 1.26896100e+00, 1.74332882e+00, 2.39502662e+00, 3.29034456e+00,
                    4.52035366e+00, 6.21016942e+00, 8.53167852e+00, 1.17210230e+01, 1.61026203e+01, 2.21221629e+01,
                    3.03919538e+01, 4.17531894e+01, 5.73615251e+01, 7.88046282e+01, 1.08263673e+02, 1.48735211e+02,
                    2.04335972e+02, 2.80721620e+02, 3.85662042e+02, 5.29831691e+02, 7.27895384e+02, 1.00000000e+03]
        x_temp_range = [5.00000000e+00, 6.49828306e+00, 8.44553654e+00, 1.09762974e+01, 1.42654175e+01, 1.85401442e+01,
                        2.40958210e+01, 3.13162930e+01, 4.07004273e+01, 5.28965794e+01, 6.87473892e+01, 8.93479989e+01,
                        1.16121718e+02, 1.50918358e+02, 1.96142042e+02, 2.54917301e+02, 3.31304956e+02, 4.30582677e+02,
                        5.59609623e+02, 7.27300347e+02, 9.45240704e+02, 1.22848833e+03, 1.59661298e+03, 2.07504862e+03,
                        2.69685066e+03, 3.50497979e+03, 4.55527016e+03, 5.92028698e+03, 7.69434011e+03, 1.00000000e+04]
    # Get the attribute values from the experiment object
    my_attrs = [getattr(exp, attr) for attr in col_list]

    # Generate all combinations of attribute values
    df_array = np.array(list(itertools.product(*my_attrs)))

    # Create a DataFrame with the combinations
    df = pd.DataFrame(df_array, columns = col_list)
    if 'cc_step' in exp.intervention_list: #im only including this because itertools.product includes repeats were output_target equal cc_change, if this could be avoided it should be
        df = df[df['output_target'] != df['cc_change']]
        df = df.reset_index(drop=True)
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

        if exp.calibrun:
            if 'MalSim' in exp.models_to_run or 'MalSim' in exp.models_to_run_pickup:
                for i, row in df.iterrows():
                    df.loc[i, 'model_input_ms'] = eir_range[int(df.loc[i, 'output_target'])-1]
            if 'OpenMalaria' in exp.models_to_run or 'OpenMalaria' in exp.models_to_run_pickup:
                for i, row in df.iterrows():
                    df.loc[i, 'model_input_om'] = eir_range[int(df.loc[i, 'output_target'])-1]
            if 'EMOD' in exp.models_to_run or 'EMOD' in exp.models_to_run_pickup:
                for i, row in df.iterrows():
                    df.loc[i, 'model_input_em'] = x_temp_range[int(df.loc[i, 'output_target'])-1]
        else:
            # Alignment of model transmission input to target outcome
            if 'MalSim' in exp.models_to_run or 'MalSim' in exp.models_to_run_pickup:
                df['model_input_ms'] = output_target_to_eir(df, exp, model = 'MalSim')
            if 'OpenMalaria' in exp.models_to_run or 'OpenMalaria' in exp.models_to_run_pickup:
                df['model_input_om'] = output_target_to_eir(df, exp, model = 'OpenMalaria')
            if 'EMOD' in exp.models_to_run or 'EMOD' in exp.models_to_run_pickup:
                if exp.entomology_mode =='dynamic':
                    df['model_input_em'] = output_target_to_xTemp(df, exp, model = 'EMOD')
                if exp.entomology_mode =='forced':
                    df['model_input_em'] = output_target_to_eir(df, exp, model = 'EMOD')

        if 'cc_step' in exp.intervention_list:
            from scenario_inputs.intervention_params import cc_step_factor_calculator, cc_title_function
            if 'MalSim' in exp.models_to_run or 'MalSim' in exp.models_to_run_pickup:
                df['cc_factor_ms'] = cc_step_factor_calculator(df, exp, model = 'MalSim')
                df['cc_timestep_ms'] = exp.cc_timestep_ms
            if 'OpenMalaria' in exp.models_to_run or 'OpenMalaria' in exp.models_to_run_pickup:
                df['cc_factor_om'] = cc_step_factor_calculator(df, exp, model = 'OpenMalaria')
                df['cc_timestep_om'] = exp.cc_timestep_om
            if 'EMOD' in exp.models_to_run or 'EMOD' in exp.models_to_run_pickup:
                df['cc_factor_em'] = cc_step_factor_calculator(df, exp, model = 'EMOD')
                df['cc_timestep_em'] = exp.cc_timestep_em
            df['cc_title'] = cc_title_function(df)
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
                        custom_args='--modelname EMOD OpenMalaria MalSim', t='05:00:00', memG=20, job_id_EMOD=False,
                        job_id_MalSim=False, job_id_OpenMalaria=False,
                        job='pyjob', write_only=False):
    """
    Submits a job to run a Python script.

    Args:
        exp (Experiment): The experiment object containing job directory and other information.
        pyscript (str, optional): The name of the Python script to run. Defaults to 'plot_benchmark.py'.
        shname (str, optional): The name of the shell script to submit. Defaults to 'run_benchmark_plots.sh'.
        custom_args (str, optional): Custom arguments to pass to the Python script. Defaults to '--modelname EMOD OpenMalaria MalSim'.
        t (str, optional): Wall time for the job in the format 'HH:MM:SS'. Defaults to '01:00:00'.
        memG (int, optional): Memory required for the job in GB. Defaults to 1.
        job_id_EMOD (bool, optional): The job ID will be set as a dependency for EMOD. Defaults to False.
        job_id_MalSim (bool, optional): The job ID will be set as a dependency for malariasimulation. Defaults to False.
        job_id_OpenMalaria (bool, optional): The job ID will be set as a dependency for OpenMalaria. Defaults to False.
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
    dependencies = '--dependency=afterany:'
    prior_dependency = False
    # Check if job_id is provided as a string to define dependendies
    if not write_only:
        if job_id_EMOD:
            id_EMOD = open(os.path.join(exp.job_directory, 'job_id_EMODanalyze.txt')).read().strip()
            dependencies = dependencies + f'{id_EMOD}'
            prior_dependency = True
        # Check if job_id_MalSim is provided as a string
        if job_id_MalSim:
            id_MalSim = open(os.path.join(exp.job_directory, 'job_id_MalSim_analyze.txt')).read().strip()
            if prior_dependency:
                dependencies = dependencies + f',{id_MalSim}'
            else:
                dependencies = dependencies + f'{id_MalSim}'
                prior_dependency = True
        if job_id_OpenMalaria:
            id_OpenMalaria = open(os.path.join(exp.job_directory, 'job_id_OManalyze.txt')).read().strip()
            if prior_dependency:
                dependencies = dependencies + f',{id_OpenMalaria}'
            else:
                dependencies = dependencies + f'{id_OpenMalaria}'
        # Submit job with dependency
        if not job_id_EMOD and not job_id_MalSim and not job_id_OpenMalaria:
            # Submit job without dependency
            p = subprocess.run(['sbatch', '--parsable', script_path], stdout=subprocess.PIPE,
                               cwd=str(exp.job_directory))
        else:
            p = subprocess.run(['sbatch', '--parsable', dependencies, script_path], stdout=subprocess.PIPE,
                               cwd=str(exp.job_directory))

        # Extract the SLURM job ID from the output
        slurm_job_id = p.stdout.decode('utf-8').strip().split(';')[0]

        # Print the submitted job ID
        print(f'Submitted {shname} to run {pyscript} - job id: {slurm_job_id}')


def submit_run_plotters(exp):
    # Optionally, create submission script for standardized plots and run after last simulations finished
    job_id_EMOD = False
    job_id_MalSim = False
    job_id_OpenMalaria = False
    if 'EMOD' in exp.models_to_run:
        job_id_EMOD = True
    if 'MalSim' in exp.models_to_run:
        job_id_MalSim = True
    if 'OpenMalaria' in exp.models_to_run:
        job_id_OpenMalaria = True

    plot_names_all = ['benchmark', 'timeseries', 'agecurves']
    ## ['ccstep', 'smc'] custom plotter excluded, as these only apply for specific simulation experiments
    # plot_memrequests_all = {'sampleplots' : 10,'benchmark' :10,'agecurves' :10 ,'ccstep' :20}

    ## Write  shell submission script for all, even if not running
    for plot_name in plot_names_all:
        pyscript_name = f'plot_{plot_name}.py'

        plot_memG = 20  # current default in submit_run_pyscript
        submit_run_pyscript(exp, pyscript=pyscript_name, shname=f'run_{plot_name}_plots.sh',
                            custom_args=f"--modelname {' '.join([x for x in exp.models_to_run])}",
                            job=f'{plot_name}_plots', memG=plot_memG, write_only=True)

    ## Write and run plots specified in exp.plots_to_run
    plots_to_run = [p for p in exp.plots_to_run if not p == 'sampleplots']  # exp.plots_to_run
    if exp.plots_to_run[0] == 'all':
        plots_to_run = plot_names_all

    ## Overwriting and submitting those to run
    for plot_name in plots_to_run:
        pyscript_name = f'plot_{plot_name}.py'

        plot_memG = 20  # current default in submit_run_pyscript
        if plot_name == 'ccstep':
            plot_memG = 80  ## as specified in launch_ccstep.py, could reintroduce/use mem_scaling factor

        submit_run_pyscript(exp, pyscript=pyscript_name, shname=f'run_{plot_name}_plots.sh',
                            custom_args=f"--modelname {' '.join([x for x in exp.models_to_run])}",
                            job_id_EMOD=job_id_EMOD, job_id_MalSim=job_id_MalSim, job_id_OpenMalaria=job_id_OpenMalaria,
                            job=f'{plot_name}_plots', memG=plot_memG)


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
        elif om_version == 46:
            ommodule = '\n\nmodule use /projects/b1139/OpenMalaria/om_v46/modules/ \nmodule load openmalaria\n'
        else:
            raise ValueError(f'{om_version} not a valid OpenMalaria version, available versions: 43, 46')
    if location == 'SCICORE':
        if om_version == 43:
            ommodule = '\n\nmodule load OpenMalaria/43.1-iomkl-2019.01\n'
        elif om_version == 46:
            ommodule = '\n\nmodule load OpenMalaria/46.0-iomkl-2019.01\n'
        else:
            raise ValueError(f'{om_version} not a valid OpenMalaria version, available versions: 43, 46')
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
