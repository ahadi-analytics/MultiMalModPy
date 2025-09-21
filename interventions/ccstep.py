import os
import pandas as pd
import numpy as np
# Carrying Capacity step change (ccstep)

def ccstep_params(exp):
    """
    This function sets up the exp object so that the carrying capacity perterbation can occur.

    Parameters:
        exp: Experiment object.

    Returns:
        Experiment object
            An object with updated experiment parameters.
    """    
    exp.ccstep = [x[1] for x in exp.target_output_values]
    exp.target_output_values = [x[0] for x in exp.target_output_values]

    exp.step_in_years = 5 # determines after x amount of years, when the carrying capacity change occurs

    if exp.emod_step is None:
        ## if None, no serialization done, hence burnin period is added to the step_in_years
        exp.cc_timestep_EMOD = int((exp.emod_burnin + exp.step_in_years) * 365)
    else:
        # 5 years in to the pickup time EMOD and malariasimulation, this parameter can already be defined in burnin for the respective pickup run
        exp.cc_timestep_EMOD = int(exp.step_in_years * 365)
    
    exp.cc_timestep_malariasimulation = int((exp.malariasimulation_burnin + exp.step_in_years) * 365)

    # 5 Years in to the pickup time OpenMalaria
    exp.openmalaria_survey_step = '5d'
    exp.cc_timestep_OpenMalaria = int((73 * (exp.openmalaria_burnin + exp.step_in_years)))

    # Required for flagging list items when running from CSV
    exp.sim_params_list += ['eir_scalar_malariasimulation', 'eir_malariasimulation', 'eir_scalar_openmalaria',
                     'eir_scalar_emod',  'eir_openmalaria', 'eir_scalar_openmalaria', 'carrying_capacity_step']
    
    if 'ccstep' not in exp.plots_to_run:
        exp.plots_to_run = exp.plots_to_run + ['ccstep']
    if '5day' not in exp.analyzer_list:
        exp.analyzer_list = exp.analyzer_list + ['5day']
    # Add ccstep to the list of sweep parameters
    if 'ccstep' not in exp.sweep_list:
        exp.sweep_list = exp.sweep_list + ['ccstep']
    if 'ccstep' not in exp.intervention_analyzer_columns:
        exp.intervention_analyzer_columns = exp.intervention_analyzer_columns + ['cc_title']

    # Flexible parameters depending on type of run and user-specifications
    if exp.run_mode == 'production':
        print('Warning: Running ccstep in production mode with pre-defined not user-defined parameters')
        exp.mem_increase_factor = 6.0  # scaling factor on default memory requested
        exp.start_year = 1995
        exp.end_year = 2050
        exp.emod_memory_per_sim = 6
        exp.emod_time_per_sim = '3:59:00'
        exp.malariasimulation_memory_per_sim = 6
        exp.malariasimulation_time_per_sim = '2:00:00'
        exp.openmalaria_memory_per_sim = 6
        exp.openmalaria_time_per_sim = '2:00:00'
    
    if exp.emod_importation_rate == 0 and exp.cc_decreasing:
        print('Warning: You are running EMOD simulations with a decreasing carrying capacity.\nWithout importation, elimination can occur.')
    if len(exp.target_output_values) < 2:
        raise ValueError(f'Please specify at least 2 output targets, for cc step to increase/decrease to.')
    return exp


def ccstep_factor_calculator(exp, df, model):
    """
    Calculates scaling factors for the `ccstep` intervention.
    This function computes adjustment factors for the `ccstep` intervention by interpolating
    values from a model-specific dataset. It takes input from a DataFrame `df`, an experiment
    object `exp`, and a model name `model`. The function performs the calculations using
    interpolation of prevalence or population size values and adjusts the output based on the
    simulated population size.

    Args:
        df (pd.DataFrame): A DataFrame containing data for calculations, with columns including:
            - `cm_clinical`
            - `seasonality`
            - `target_output_values`
            - `ccstep`
        exp (object): An object representing the experiment, which should include:
            - `interp_path` (str): Path to the folder containing interpolation data.
            - `interp_csv` (str): Name of the CSV file for interpolation.
            - `pop_size` (int): Population size for scaling factors.
        model (str): Name of the model used for interpolation. Supported values are `EMOD`
            and `OpenMalaria`.

    Returns:
        list[float]: A list of correction factors calculated for each row in the input DataFrame.

    Raises:
        ValueError: If the interpolation file (`interp_csv`) is not found in the specified path.

    Notes:
        - The function expects the interpolation file to contain columns:
          `cm_clinical`, `seasonality`, `models`, `pop_size`, `prevalence_2to10`, and
          either `input_target` or `n_total_mos_pop` depending on the model.
        - Population size scaling is applied to ensure compatibility with model fitting.

    """

    interp_path = os.path.join(exp.interp_path, model, exp.interp_csv)
    if not os.path.exists(interp_path):
        raise ValueError(f'interp_file not found: {interp_path}')
    data = pd.read_csv(interp_path)
    output = []

    if model == 'EMOD':
        popsize = exp.emod_pop_size
    elif model == 'malariasimulation':
        popsize = exp.malariasimulation_pop_size
    elif model == 'OpenMalaria':
        popsize = exp.openmalaria_pop_size
    else:
        raise ValueError(f'Specified model is not valid {model}')

    # NOTE: Workaround to allow smaller populations for test runs
    if exp.test and popsize not in data.loc[data['models'] == model, 'pop_size'].unique():
        popsize = data.loc[data['models'] == model, 'pop_size'].min()
            
    for i, row in df.iterrows():
        idata = data[((data['cm_clinical'] == row['cm_clinical'])
                      & (data['cm_severe'] == row['cm_severe'])
                      & (data['seasonality'] == row['seasonality'])
                      & (data['models'] == model)
                      & (data['pop_size'] == popsize))]
        if model == 'EMOD':
            xt = idata[exp.target_output_name]
            yp = idata['input_target']
            xold = row['target_output_values']
            xnew = row['ccstep']
            interpolated_old = np.interp(xold, xt, yp)
        else:
            xt = idata[exp.target_output_name]
            yp = idata['n_total_mos_pop']
            xold = row['target_output_values']
            xnew = row['ccstep']
            interpolated_old = np.interp(xold, xt, yp)
        interpolated_new = np.interp(xnew, xt, yp)

        if model == 'OpenMalaria':
            interpolated_value = 1 - (interpolated_new / interpolated_old)
        else:
            interpolated_value = interpolated_new / interpolated_old
        output.append(interpolated_value)
    return output


def cc_title_function(df):
    """
    Generates a list of formatted strings representing percentage change titles
    based on the values in the provided DataFrame.

    Each row in the DataFrame contributes one title, formatted as:
    "<target_output_values>% - <ccstep>%", where:
    - `target_output_values` and `ccstep` are multiplied by 100 and converted to integers
      to represent percentage values.

    Args:
        df (pandas.DataFrame): A DataFrame containing the following columns:
            - `target_output_values` (float): The starting value for the percentage change.
            - `ccstep` (float): The change value for the percentage change.

    Returns:
        list[str]: A list of strings, where each string is a formatted title
                   representing the percentage change for a row.
    """
    output = []
    for i, row in df.iterrows():
        first_percent = int(float(row['target_output_values']) * 100)
        to_percent = int(float(row['ccstep']) * 100)
        title = f'{first_percent}%-{to_percent}%'
        output.append(title)
    return output


def ccstep_columns(exp, df):
    """
    Adds columns for CC steps if present.

    Args:
        exp (Experiment): The experiment object.
        df (pandas.DataFrame): The DataFrame.

    Returns:
        pandas.DataFrame: Updated DataFrame.
    """

    for model in ['EMOD', 'malariasimulation', 'OpenMalaria']:
        if model in exp.models or model in exp.models_pickup:
            df[f'cc_factor_{model}'] = ccstep_factor_calculator(exp, df, model=model)
            df[f'cc_timestep_{model}'] = getattr(exp, f'cc_timestep_{model}')
    df['cc_title'] = cc_title_function(df)
    return df  # TODO can be moved to postprocessing



def ccstep_input_check(exp):
    if exp.entomology_mode != "dynamic":
        raise ValueError(f'Invalid entomology_mode for ccstep {exp.entomology_mode} specified, "dynamic" required')
    #if exp.target_output_name != 'prevalence_2to10':
    #    raise ValueError("ccstep requires the target_output_name to be prevalence_2to10")
    if exp.end_year - exp.start_year < exp.step_in_years:
        raise ValueError(f"step_in_years ({exp.step_in_years} years) falls outside of the range of {exp.start_year} and {exp.end_year}")
