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


def output_target_to_xTemp(df, exp,  model):
    """
    Interpolates and adjusts the output target to the `x_Temporary_Larval_Habitat` parameter based on input data
    for different models and experimental conditions.

    Args:
        df (pd.DataFrame): DataFrame containing simulation job data, with each row representing a specific condition
            (e.g., `output_target`, `cm_clinical`, `seasonality`).
        exp (Experiment): Experiment object that contains attributes such as `interp_path`, `output_type`, `pop_size`,
            and others required for interpolation.
        model (str): The model name used in the interpolation (e.g., 'malariasimulation', 'OpenMalaria').

    Returns:
        list: A list of interpolated `x_Temporary_Larval_Habitat` values corresponding to each row of the input DataFrame.

    Raises:
        ValueError: If the interpolation file is not found at the specified path.
        ValueError: If the `output_type` specified in the experiment object is not valid.

    Notes:
        - The function performs interpolation based on the specified output type (`eir`, `prevalence_2to10`, or
          `clinical_incidenceU5`).
        - It applies scaling adjustments for population sizes, ensuring that the values are consistent with the
          `pop_size` defined in the experiment.
        - Warnings are issued if the interpolated values are outside the valid range (`<= 0` or `>= 10000`), with
          adjustments made to these values accordingly.
    """
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
                      & (data['modelname'] == model)
                      & (data['pop_size'] == exp.emod_pop_size))]
        xt = idata[output_type_col]
        yp = idata['input_target']
        xnew = row['output_target']
        interpolated_value = np.interp(xnew, xt, yp)

        if interpolated_value <= 0:
            interpolated_value = 0.01
            print(
                "Warning: EMOD's x_Temporary_Larval_Habitat < 0, value set to 0.01 (this will likely cause elimination in the simulations)")
        if interpolated_value >= 10000:
            interpolated_value = 10000
            print(
                "Warning: EMOD's x_Temporary_Larval_Habitat > 10000, value set to 10000 (higher values cannot be reasonably simulated)")
        output.append(interpolated_value)
    return output


def output_target_to_eir(df, exp, model):
    """
    Interpolates and adjusts the output target to the expected EIR (Entomological Inoculation Rate) values
    based on input data for different models and experimental conditions.

    Args:
        df (pd.DataFrame): DataFrame containing simulation job data, where each row represents a specific condition
            (e.g., `output_target`, `cm_clinical`, `seasonality`).
        exp (Experiment): Experiment object that contains attributes such as `interp_path`, `output_type`, `pop_size`,
            and others required for interpolation.
        model (str): The model name used in the interpolation (e.g., 'malariasimulation', 'OpenMalaria').

    Returns:
        list: A list of interpolated EIR values corresponding to each row of the input DataFrame.

    Raises:
        ValueError: If the interpolation file is not found at the specified path.
        ValueError: If the `output_type` specified in the experiment object is not valid.

    Notes:
        - The function performs interpolation based on the specified output type (`eir`, `prevalence_2to10`, or
          `clinical_incidenceU5`).
        - It applies scaling adjustments for population sizes, ensuring that the values are consistent with the
          `pop_size` defined in the experiment.
        - Warnings are issued if the interpolated values are outside the valid range (`<= 0` or `>= 1000`), with
          adjustments made to these values accordingly.
    """
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
    if model == 'EMOD':
        popsize = exp.emod_pop_size
    elif model == 'malariasimulation':
        popsize = exp.malariasimulation_pop_size
    elif model == 'OpenMalaria':
        popsize = exp.openmalaria_pop_size
    else:
        raise ValueError(f'Specified model is not valid {model}')    
    
    for i, row in df.iterrows():
        idata = data[((data['cm_clinical'] == row['cm_clinical'])
                      & (data['seasonality'] == row['seasonality'])
                      & (data['modelname'] == model)
                      & (data['pop_size'] == popsize))]
        xt = idata[output_type_col]
        yp = idata['input_target']
        xnew = row['output_target']
        interpolated_value = np.interp(xnew, xt, yp)
        if interpolated_value <= 0:
            interpolated_value = 0.01
            print("Warning: eir < 0, value set to 0.01 (this will likely cause elimination in the simulations)")
        if interpolated_value >= 1000:
            interpolated_value = 1000
            print("Warning:  eir > 1000, value set to 1000 (higher values cannot be reasonably simulated)")
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


def get_simulation_time_params(exp):
    """
    Calculates simulation time parameters for EMOD, malariasimulation and OpenMalaria based on the provided arguments.

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
    end_year = exp.end_year
    models_to_run = exp.models_to_run
    emod_step = exp.emod_step

    # Calculate the number of years to monitor
    monitoring_years = end_year - start_year

    if emod_step is None:
        if 'EMOD' in models_to_run:
            print(" --------| Running EMOD burnin + pickup time in one simulation run |--------")
        burnin_start_year = start_year - exp.emod_burnin
        sim_dur_years = end_year - burnin_start_year
        sim_start_year = burnin_start_year
    elif emod_step == 'burnin':
        if 'EMOD' in models_to_run:
            print(" --------| Running EMOD burnin (step 1) |--------")
        sim_dur_years = exp.emod_burnin
        burnin_start_year = start_year - exp.emod_burnin
        sim_start_year = burnin_start_year
    elif emod_step == 'pickup':
        if 'EMOD' in models_to_run:
            print(" --------| Running EMOD pickup from serialized burnin (step 2) |--------")
        sim_dur_years = end_year - start_year
        sim_start_year = start_year
    else:
        raise ValueError(f'Please specify valid emod_step, {emod_step} is not valid')

    # Update experiment object with simulation start year and duration
    exp.sim_start_year_emod = sim_start_year
    exp.sim_start_year_openmalaria = start_year - exp.openmalaria_burnin
    exp.sim_start_year_malariasimulation = start_year - exp.malariasimulation_burnin
    exp.monitoring_years = monitoring_years
    exp.sim_dur_years = sim_dur_years
    return exp


def param_variation(df, exp):
    """
    Perform parameter variation for malariasimulation simulations.

    Parameters:
    - df: DataFrame containing data from scenarios.csv.
    - exp: Experiment object.

    Returns:
    DataFrame with added column 'malariasimulation_pv' representing malariasimulation parameter variation values.
    """
    if exp.malariasimulation_parameter_variation and 'malariasimulation' in exp.models_to_run:
        from random import sample
        if exp.num_seeds > 1000:
            print("Warning: num_seeds > 1000, therefore malariasimulation parameter variation will have repeat values")
            par_var = [(i % 1000) + 1 for i in sample(range(1, exp.num_seeds + 1), exp.num_seeds)]
            for i, row in df.iterrows():
                df.loc[i, 'malariasimulation_pv'] = int(par_var[df.loc[i, 'seed'] - 1])
        else:
            par_var = sample(range(1, 1001), exp.num_seeds)
            for i, row in df.iterrows():
                df.loc[i, 'malariasimulation_pv'] = int(par_var[df.loc[i, 'seed'] - 1])
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