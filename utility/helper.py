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
#from idmtools.entities.experiment import Experiment
from utility.helper_slurm import *
from utility.helper_simulation import *

def parse_launch_args():
    parser = argparse.ArgumentParser(description="Description of your script.")

    # Define command-line arguments with default values
    parser.add_argument("-d", "--directory",
                        type=str,
                        required=False,
                        help="Jobdirectory of burnin, if no EMOD burnin, is ignored")
    parser.add_argument('--suite',
                        type=str,
                        default=f'test_{dt.now().strftime("%Y%m%d")}',
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
    parser.add_argument('-r', '--run_mode',
                        type=str,
                        default=None,
                        choices=[None, 'test', 'calibrun', 'productionrun'],
                        help='Specify whether to run a normal run, a test run, calibration run or production run, population and burnin and seeds will be adjusted automatically')
    parser.add_argument('--emod_calib_params',
                        action='store_true',
                        help='Specify whether to run including calibration parameters as a sweep variable (EMOD only)')
    parser.add_argument('--mpv',
                        default=True,
                        type=bool,
                        help='Specify whether to run malariasimulation with parameter variation, default is to run parameter variation')
    parser.add_argument('--output_type',
                        type=str,
                        default='prevalence_2to10',
                        choices=['prevalence_2to10','eir'], # clinical_incidenceU5 #
                        help='Specify whether to align transmission in each model by EIR or by prevalence_2to10') # , or by clinical incidence
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

    # list of parameters expecting list format
    listparams = ['seasonality', 'sweep_list', 'cm_clinical', 'output_target', 'intervention_list', 'agebins' ]

    value = df[name].iat[0]

    if name in listparams:
        try:
            out = value.replace(' ', '').split(',')
            out = [float(i) if i.replace('.', '', 1).isdigit() else i for i in out]
        except:
            out = [value]
    else:
        out = value

    return out


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
            os.makedirs(os.path.join(exp.sim_out_dir, '../MalSim'), exist_ok=overwrite)
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


# check inputs to be run after all exp parameters were updated, i.e. after exp_params_to_update
def check_exp_inputs(exp, print_reminder = True, intervention_checks = True, attribute_check= False):
    """
    Helper function to validate experiment inputs.

    Args:
        exp (Experiment): Custom object containing experiment specifications.

    Raises:
        ValueError: If input parameters are invalid.
    """

    if print_reminder:
        print(f'Reminder: Importation is currently set to {exp.importation_rate}')


    # Check timesteps, survey intervals and analyer alignment
    if exp.om_survey_step == '30d' and "5day" in exp.analyzer_list:
        print('Warning: OpenMalaria runs with 30d survey steps , 5day analyzer will cause an error in postprocessing')

    if exp.om_survey_step == '30d' and "cc_step" in exp.intervention_list:
        raise ValueError('cc_step interventions requires 5d survey steps in OpenMalaria')

    if exp.emod_step:
        if exp.num_seeds_burnin != 1:
            raise ValueError('Current framework only allows 1 seed for EMOD burnin')

    if exp.burnin < 80 and (('EMOD' in exp.models_to_run and exp.emod_step != 'pickup') or
                            'EMOD' not in exp.models_to_run):
        print('Warning: Short burnin period of {exp.burnin} years. A burnin of at least 80 years is recommended.')

    # Check agebins
    a = {age for interval in exp.age_groups_aggregates for age in interval if age != 0 and age not in exp.agebins}
    if len(a) > 0:
        raise ValueError(f'agebins are not granular enough to allow aggregation by age_groups_aggregates, missing {a}')

    if 2 not in exp.agebins or 10 not in exp.agebins:
        raise ValueError(f'agebins 2 and 10 are required in the framework, current agebins {exp.agebins}')

    # Check unique limitations of framework that are in process/not yet working
    if len(exp.seasonality) > 1:
        raise ValueError(f'Only one seasonality pattern is allowed, but {len(exp.seasonality)} specified.')

    # Check whether parameters align with current setup in calibruns - "interpolation data"
    if any(value not in [0, 0.45] for value in exp.cm_clinical) and (exp.entomology_mode == 'dynamic') and ('EMOD' in exp.models_to_run):
        raise ValueError('EMOD is not set up to run dynamic EIR is not set up to run for CM values other than 0 and 0.45 - requires new calibrun')

    if any(value not in [0, 0.45] for value in exp.cm_clinical) and exp.output_type == 'prevalence_2to10':
        raise ValueError('output_type prevalence_2to10 is not set up to run for CM values other than 0 and 0.45 - requires new calibrun')

    if exp.output_type not in ['eir', 'prevalence_2to10']:
        raise ValueError(f"Invalid output type: {exp.output_type}")

    # Check for interventions added to the framework
    if intervention_checks:
        if "cc_step" in exp.intervention_list :
            if exp.entomology_mode != "dynamic":
                raise ValueError( f'Invalid entomology_mode for cc_step {exp.entomology_mode} specified, but "dynamic" required')
            if exp.output_type != 'prevalence_2to10' :
                raise ValueError("cc_step requires the output_type to be prevalence_2to10")
            if exp.end_year - exp.start_year < exp.step_in_years:  # check inputs to be run after all exp parameters were updated
                raise ValueError(f"step_in_years ({exp.step_in_years} years) falls outside of the range of {exp.start_year} and { exp.end_year}")

    # Check if any attribute in list_attributes_nGT1 is not in sweep_list
    if attribute_check:
        attributes_dict = exp.__dict__
        list_attributes_nGT1 = list()

        for key, value in attributes_dict.items():
            # Check if the attribute is a list
            if isinstance(value, list) and len(value) > 1:
                if key not in ['models_to_run', 'eir_scalar_emod', 'eir_malsim', 'eir_scalar_malsim', 'eir_om',
                               'eir_scalar_om', 'carrying_capacity_step', 'age_groups_aggregates', 'plots_to_run',
                               'agebins', 'sweep_list', 'season_daily', 'season_month', 'seasonal', 'perennial',
                               'analyzer_list', 'analyzer_script', 'calib_config_pointer', 'models_to_run_pickup']:
                    list_attributes_nGT1.append(key)

        list_attr_notsweep = [attr for attr in list_attributes_nGT1 if attr not in attributes_dict['sweep_list']]
        if list_attr_notsweep:
            raise ValueError(f'The following attributes have more than 1 value but are not included in sweep_list: {", ".join(list_attr_notsweep)}')


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
    setup_dic = {'run_mode': exp.run_mode,
                 'job_directory': exp.job_directory,
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

    if exp.run_mode == 'calibrun':
        print("Notice: for calibrun simulations, importation will be set to 0")
        print("Depending on EM/OM Performance at lower EIRS at 50k pop, this may change")
        exp.importation_rate = 0
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

        if exp.run_mode == 'calibrun':
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
