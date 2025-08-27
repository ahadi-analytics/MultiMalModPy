import argparse
import os
import itertools
import pickle
from datetime import datetime as dt
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
# from idmtools.entities.experiment import Experiment
from utility.helper_slurm import *
from utility.helper_simulation import *
from utility.helper_calibration import output_target_to_xTemp, output_target_to_eir
from utility.helper_interventions import intervention_params_to_check


def parse_launch_args():
    """
    Parses command-line arguments for launching a simulation experiment.

    This function defines and parses several command-line arguments required for running a simulation experiment.
    The arguments specify parameters such as the job directory, suite name, experiment name, model to run, user directory,
    interventions, run mode, and output type. The parsed arguments are returned as a Namespace object.

    Args:
        None

    Returns:
        argparse.Namespace: An object containing the parsed command-line arguments.

    Command-Line Arguments:
        -d, --directory (str)       : Job directory for burn-in; ignored if no EMOD burn-in is provided.
        --suite (str)               : Name of the suite; defaults to the current date followed by "_test".
        --expname (str)             : Name of the experiment; defaults to include the current time.
        --emodstep (str)            : Specifies the EMOD step (e.g., 'burnin', 'pickup', 'new_pickup').
        --serializedid (str)        : Serialized ID for EMOD, if applicable.
        --models (list)             : List of models to run (default: ['EMOD', 'malariasimulation', 'OpenMalaria']).
        --user (str)                : Subdirectory for simulations, based on the current user or 'b1139' for NUCLUSTER.
        --csv (str)                 : Name of the scenario CSV file.
        --rownum (int)              : Row number from the specified scenario CSV (default: 0).
        -r, --run_mode (str)        : Type of run ('custom', 'calibration', 'simple', 'production', or 'csv').
        --emod_calib_params (bool)  : Whether to include calibration parameters for EMOD.
        --mpv (bool)                : Whether to run malariasimulation with parameter variation (default: True).
        -t, --test (bool)           : Runs the simulation with lower population, shorter burn-in, and fewer seeds.
        -n, --note (str)            : An optional tag to distinguish different runs.
    """
    parser = argparse.ArgumentParser(description="Description of your script.")

    # Define command-line arguments with default values
    parser.add_argument("-d", "--directory",
                        type=str,
                        required=False,
                        help="Job directory for burn-in; ignored if no EMOD burn-in is used.")
    parser.add_argument('--suite',
                        type=str,
                        default=f'{dt.now().strftime("%Y%m%d")}',
                        help="Name of the suite (default: current date).")
    parser.add_argument('--expname',
                        type=str,
                        default=f'sims_entomologymode_seasonality_intervention_{dt.now().strftime("%H_%M_%S")}',
                        help="Experiment name (default: includes timestamp).")
    parser.add_argument('--emodstep',
                        type=str,
                        default=None,
                        choices=[None, 'burnin', 'pickup', 'new_pickup'],
                        help="Step for EMOD: 'burnin', 'pickup', or 'new_pickup'.")
    parser.add_argument('--serializedid',
                        type=str,
                        default='',
                        help='Serialized ID for EMOD, if applicable.')
    parser.add_argument('-m','--models',
                        nargs='+',
                        default=['EMOD', 'malariasimulation', 'OpenMalaria'],
                        choices=['EMOD', 'malariasimulation', 'OpenMalaria'],
                        help="List of malaria models to run - any combination of ['EMOD', 'malariasimulation', 'OpenMalaria'].")
    parser.add_argument('--user',
                        type=str,
                        default=os.environ.get('USER'),
                        help='User subdirectory for simulations (default: system username).')
    parser.add_argument('--csv',
                        type=str,
                        required=False,
                        help='Name of the scenario CSV file.')
    parser.add_argument('--rownum',
                        type=int,
                        default=0,
                        help='Row number in the scenario CSV file (default: 0).')
    parser.add_argument('-r', '--run_mode',
                        type=str,
                        default='custom',
                        choices=['custom','calibration', 'simple', 'production', 'csv'],
                        help="Simulation run type (default: 'custom').")
    parser.add_argument('--emod_calib_params',
                        action='store_true',
                        help='Include calibration parameters for EMOD (default: False).')
    parser.add_argument('--mpv',
                        action='store_true',
                        help='Run malariasimulation with parameter variation (default: False).')
    parser.add_argument('-t','--test',
                        action='store_true',
                        help='Enable test mode with reduced population, burn-in, and seeds.')
    parser.add_argument('-n','--note',
                        type=str,
                        default='',
                        help='Optional tag for distinguishing runs.')
    args = parser.parse_args()

    # Validate CSV and rownum combination
    if args.csv:
        if args.rownum is None:
            print(f"The '--csv' argument was specified ({args.csv}) but no rownum"
                   "Using default 'rownum' 0 to run first row")
        args.run_mode = "csv"
        print(f"The '--csv' argument was specified ({args.csv}). "
              "Setting 'run_mode' to 'csv'.")

    # Ensure EMOD is specified if emodstep is set
    if args.emodstep is not None and 'EMOD' not in args.models:
        raise ValueError(f"EMOD is not specified in the models list, but emodstep is set to {args.emodstep}. "
                         "Did you forget to include EMOD in models?")

    # Warning for experimental feature
    if args.emodstep == 'new_pickup':
        print("Warning: 'new_pickup' is in development mode. Please review your simulation and results carefully.")

    return args


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


def get_param_from_dataframe(df, name, sim_params_list):
    """
    Retrieves a parameter value from a DataFrame and returns it in the correct format for storage in an experiment object (exp).

    Example:
        exp.seasonality = get_param_from_dataframe(exp_scen_df, 'seasonality', listparam=True)

    Args:
        df (pandas.DataFrame): The DataFrame containing the parameter value.
        name (str): The name of the parameter.
        sim_params_list (List[str]): List of parameter names expected to be lists.

    Returns:
        Union[list, str]: The parameter value, either as a list or a string, based on the 'listparam' argument.

    """

    value = df[name].iat[0]

    if name == "case_management":
        import ast
        out = ast.literal_eval(f'[{value}]')
        out = [float(i) if isinstance(i, str) and i.replace('.', '', 1).isdigit() else i for i in out]
    else:
        if name in sim_params_list:
            try:
                out = value.replace(' ', '').split(',')
                out = [float(i) if i.replace('.', '', 1).isdigit() else i for i in out]
            except:
                out = [value]
        else:
            out = value

    if isinstance(out, list) and len(out) == 1:
        v = out[0]
        if v is None or v != v:
            return []

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
    exp.output_directory = os.path.join(exp.output_directory_manifest, exp_suite_path,
                                   exp.exp_name)  # stores results csvs and figures

    # Create directories
    os.makedirs(exp.job_directory, exist_ok=overwrite)
    os.makedirs(os.path.join(exp.job_directory, 'log'), exist_ok=overwrite)
    os.makedirs(exp.output_directory, exist_ok=overwrite)

    # Create subdirectories for specific simulation models included in exp.models
    if 'EMOD' in exp.models:
        os.makedirs(os.path.join(exp.output_directory, 'EMOD'), exist_ok=overwrite)

    if exp.emod_step != 'burnin':
        if 'OpenMalaria' in exp.models:
            os.makedirs(os.path.join(exp.output_directory, 'OpenMalaria'), exist_ok=overwrite)
        if 'malariasimulation' in exp.models:
            os.makedirs(os.path.join(exp.output_directory, 'malariasimulation'), exist_ok=overwrite)
    return exp


def exp_obj_to_csv(file_path):
    """
    Converts the experiment object (stored as a pickle file) to a CSV file.

    This function reads a pickle file containing an experiment object (`exp.obj`), and then converts it to a CSV
    file format (`exp_obj.csv`). The function supports two data types: dictionaries and lists.
    - If the data is a dictionary, it writes each key-value pair to the CSV with columns "Key" and "Value".
    - If the data is a list, it writes each item in the list as a row in the CSV (assuming each item is a list or tuple).

    Args:
        file_path (str): Path to the directory where the pickle file (`exp.obj`) is located and where the CSV file will be saved.

    """
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
def check_exp_inputs(exp, attribute_check=False):
    """
    Helper function to validate experiment inputs.

    Args:
        exp (Experiment): Custom object containing experiment specifications.

    Raises:
        ValueError: If input parameters are invalid.
    """

    if exp.hpc == 'LOCAL' and not exp.test :
        raise ValueError("Local execution of the framework is only permitted for test runs.")

    ## Generell check on input parameter combinations and formats
    check_exp_input_parameters(exp)

    # Check whether parameters align with current setup in calibruns - "interpolation data"
    from utility.helper_calibration import check_transmission_targets_input
    if exp.run_mode != 'calibration':
        check_transmission_targets_input(exp)

    ## Model specific checks
    if 'OpenMalaria'  in exp.models:
        check_exp_inputs_openmalaria(exp)

    if 'EMOD' in exp.models:
        check_exp_inputs_emod(exp)

    if 'malariasimulation' in exp.models:
        check_exp_inputs_malariasimulation(exp)

    # Check for interventions added to the framework
    intervention_params_to_check(exp)

    # Check if any attribute in list_attributes_nGT1 is not in sweep_list
    if attribute_check:
        attributes_dict = exp.__dict__
        list_attributes_nGT1 = list()

        for key, value in attributes_dict.items():
            # Check if the attribute is a list
            if isinstance(value, list) and len(value) > 1:
                if key not in ['models', 'eir_scalar_emod', 'eir_malariasimulation',
                               'eir_scalar_malariasimulation', 'eir_openmalaria',
                               'eir_scalar_openmalaria', 'carrying_capacity_step', 'age_groups_aggregates',
                               'plots_to_run',
                               'agebins', 'sweep_list', 'season_daily', 'season_month', 'seasonal', 'perennial',
                               'analyzer_list', 'analyzer_script', 'calib_config_pointer', 'models_pickup']:
                    list_attributes_nGT1.append(key)

        list_attr_notsweep = [attr for attr in list_attributes_nGT1 if attr not in attributes_dict['sweep_list']]
        if list_attr_notsweep:
            raise ValueError( f'The following attributes have more than 1 value but are not included in sweep_list: {", ".join(list_attr_notsweep)}')

    # Check eligibility of parsed args
    if exp.run_mode == "calibration" and exp.intervention_list != []:
        raise ValueError(
            "Interventions are not allowed in calibration mode. "
            "Please ensure 'exp.interventions' is an empty list when using the 'calibration' run mode."
        )


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
    Creates a CSV file containing the simulation setup parameters from the given experiment object.

    This function collects various parameters from the `exp` (Experiment) object and writes them to a CSV file.
    The CSV contains the following fields:
    - `run_mode`, `job_directory`, `output_directory`, `emod_serialized_id`, and other simulation-specific parameters.
    - Additionally, various burnin, population size, age group settings, seasonal data, and intervention lists are included.

    The resulting CSV is saved in the directories specified by `job_directory` and `output_directory`.

    Args:
        exp (Experiment): An instance of the `Experiment` class that contains experiment settings, simulation configurations,
                          and paths for output.
    """

    # If other parameters should be savedm these need to be added to setup_dic
    setup_dic = {'run_mode': exp.run_mode,
                 'job_directory': exp.job_directory,
                 'output_directory': exp.output_directory,
                 'emod_serialized_id': exp.emod_serialized_id,
                 'burnin_directory': exp.burnin_directory,
                 'entomology_mode': exp.entomology_mode,
                 'nexps': exp.nexps,
                 'sweep_list': exp.sweep_list,
                 'monitoring_years': exp.monitoring_years,
                 'pop_size_emod': exp.emod_pop_size,
                 'pop_size_malariasimulation': exp.malariasimulation_pop_size,
                 'pop_size_openmalaria': exp.openmalaria_pop_size,
                 'agebins': exp.agebins,
                 'seasonality': exp.seasonality,
                 'seasonal_monthly': ';'.join(map(str, exp.seasonal)),
                 'perennial_monthly': ';'.join(map(str, exp.perennial)),
                 'seasonal_daily': ';'.join(map(str, exp.seasonal_daily)),
                 'perennial_daily': ';'.join(map(str, exp.perennial_daily)),
                 'start_year': exp.start_year,
                 'end_year': exp.end_year,
                 'burnin_emod':exp.emod_burnin,
                 'burnin_malariasimulation': exp.malariasimulation_burnin,
                 'burnin_openmalaria': exp.openmalaria_burnin,
                 'sim_start_year_openmalaria': exp.sim_start_year_openmalaria,
                 'sim_start_year_emod': exp.sim_start_year_emod,
                 'sim_start_year_malariasimulation': exp.sim_start_year_malariasimulation,
                 'intervention_list': exp.intervention_list,
                 'interp_csv': exp.interp_csv,
                 'target_output_name': exp.target_output_name,
                 'target_output_values':  ';'.join(map(str, exp.target_output_values))
                 }

    setup_df = pd.DataFrame.from_dict(setup_dic, orient='index', columns=['Value'])
    setup_df['parameter'] = setup_df.index
    save_dirs = [exp.job_directory, exp.output_directory]
    for sdir in save_dirs:
        if not os.path.exists(sdir):
            raise OSError(f"Cannot save file into a non-existent directory: '{sdir}'")
        save_path = os.path.join(sdir, 'exp_setup_df.csv')
        setup_df.to_csv(save_path, index=False)


def process_case_management(df):
    """
    Processes and splits the case management column.

    Handles cases where `case_management` contains either a list of two values
    or a single value in a list.

    Args:
        df (pandas.DataFrame): The DataFrame.

    Returns:
        pandas.DataFrame: Updated DataFrame.
    """
    
    for i, row in df.iterrows():
        df.loc[i, 'cm_clinical'] = pd.to_numeric(df.loc[i, 'case_management'][0], errors='coerce')
        df.loc[i, 'cm_severe'] = pd.to_numeric(df.loc[i, 'case_management'][1], errors='coerce')
    df['cm_start'] = 1
    df = df.drop('case_management', axis=1)

    return df

def map_model_calib_inputs(exp, df):
    """
    Maps model inputs based on output targets.

    Args:
        exp (Experiment): The experiment object.
        df (pandas.DataFrame): The DataFrame.
    Returns:
        pandas.DataFrame: Updated DataFrame.
    """
    models = list(set(exp.models + exp.models_pickup))

    if exp.run_mode == 'calibration':
        for model in models:
            for i, row in df.iterrows():
                value = exp.eir_range[int(row['target_output_values']) - 1] if model != 'EMOD' else exp.x_temp_range[int(row['target_output_values']) - 1]
                df.loc[i, f'transmission_intensity_{model}'] = value
    else:
        for model in models:
            if model in ['malariasimulation', 'OpenMalaria']:
                df[f'transmission_intensity_{model}'] = output_target_to_eir(df, exp, model=model)
            if model == 'EMOD':
                if exp.entomology_mode == 'dynamic':
                    df['transmission_intensity_EMOD'] = output_target_to_xTemp(df, exp, model='EMOD')
                elif exp.entomology_mode == 'forced':
                    df['transmission_intensity_EMOD'] = output_target_to_eir(df, exp, model='EMOD')

    return df

def create_scenarios_csv(exp, col_list):
    """
    Generate a scenarios DataFrame based on the provided experiment object and column list.

    This function constructs a DataFrame of all possible combinations of attributes specified
    in `col_list` and maps additional experiment-specific parameters, including entomology mode,
    number of seeds, and calibration target inputs. It also processes specific interventions
    such as `ccstep` if present.

    Args:
        exp (Experiment): The experiment object containing attributes and settings for scenarios.
        col_list (list, optional): List of attribute names to include in the scenarios DataFrame.
            Defaults to ['target_output_values', 'case_management', 'seasonality'].

    Returns:
        pandas.DataFrame: A DataFrame representing all generated scenarios, including metadata
                          and mapped inputs.
    """

    if col_list is None:
        col_list = ['target_output_values', 'case_management','seasonality']

    # Get the attribute values from the experiment object
    my_attrs = [getattr(exp, attr) for attr in col_list]

    # Generate all combinations of attribute values
    df_array = list(itertools.product(*my_attrs))

    # Create a DataFrame with the combinations
    df = pd.DataFrame(df_array, columns = col_list)

    # And additional columns to keep
    df['entomology_mode'] = exp.entomology_mode # optional, same across all scenarios
    df['num_seeds'] = exp.num_seeds  # optional, same across all scenarios+seeds (total number of seeds)

    # Specifc process for clinical and severe case management (not full factorial)
    df = process_case_management(df)

    # Add calibration target inputs
    df = map_model_calib_inputs(exp, df)

    # Adjust scenarios as required for specific interventions
    from utility.helper_interventions import scenario_df_to_update
    df = scenario_df_to_update(exp, df)

    # Reset index
    df.reset_index(inplace=True)
    df['index'] = df['index'] + 1
    df['scen_id'] = df['index']

    # Move 'index' and 'scen_id' to the first two columns
    columns_order = ['index', 'scen_id'] + [col for col in df.columns if col not in ['index', 'scen_id']]
    df = df[columns_order]

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
