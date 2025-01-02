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




def get_intervention_params(exp):
    """
    Retrieve intervention parameters for a specific experiment.

    Parameters:
    - exp: Experiment object.

    Returns:
    Intervention parameters based on the specified experiment.
    """
    from utility.helper_interventions import exp_params_to_update
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
    #season_month = [2.969670822, 1.841811729, 1.327101791, 0.857686237, 0.611351676, 0.48901135,
    #                0.480399615, 0.725799099, 1.140032967, 2.215493305, 3.229497298, 3.844139468]
    # Current seasonal profile
    season_month = [0.8805187,0.3777064,0.2889602,0.2133112,0.1861301,0.2489096,
                    0.3118984,0.9748496,2.0616227,5.3832473,5.8989803,3.0026041]

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



def check_exp_input_parameters(exp):
    # Check agebins
    a = {age for interval in exp.age_groups_aggregates for age in interval if age != 0 and age not in exp.agebins}
    if len(a) > 0:
        raise ValueError(f'agebins are not granular enough to allow aggregation by age_groups_aggregates, missing {a}')

    if 2 not in exp.agebins or 10 not in exp.agebins:
        raise ValueError(f'agebins 2 and 10 are required in the framework, current agebins {exp.agebins}')

    # Check seasonality
    if len(exp.seasonality) > 2:
        raise ValueError(f'Only two seasonality patterns are allowed, but {len(exp.seasonality)} specified.')



def check_exp_inputs_emod(exp):

    if exp.emod_step:
        if exp.num_seeds_burnin != 1:
            raise ValueError('Current framework only allows 1 seed for EMOD burnin')

    if exp.emod_burnin < 100 and (('EMOD' in exp.models_to_run and exp.emod_step != 'pickup') or
                            'EMOD' not in exp.models_to_run):
        print(f'Warning: For EMOD a burnin of at least 100 years is recommended. A short burnin period of {exp.emod_burnin} years was used.')


def check_exp_inputs_openmalaria(exp):

    # Check timesteps, survey intervals and analyer alignment
    if exp.openmalaria_survey_step == '30d' and "5day" in exp.analyzer_list:
        print('Warning: OpenMalaria runs with 30d survey steps, 5day analyzer will cause an error in postprocessing')

    if exp.openmalaria_survey_step == '30d' and "cc_step" in exp.intervention_list:
        raise ValueError('cc_step interventions requires 5d survey steps in OpenMalaria')

def check_exp_inputs_malariasimulation(exp):

    pass

