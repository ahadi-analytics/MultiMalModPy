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
    season_month = [0.233157871,0.341117068,0.362055343,0.874307602,1.753063415,4.191822901,
                    6.503111076,3.762619433,0.845941712,0.30071158,0.196174256,0.215097924]

    eir_sum = sum(season_month)
    seasonal = [(x / eir_sum) for x in season_month] # rescale to sum =1
    season_daily = monthly_to_daily_EIR(seasonal)
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


def submit_run_plotters(exp):
    """
    Submits a plotter job for execution, either locally or via SLURM based on the HPC configuration:
    - If running locally, it generates and submits the plotter job using a local submission script.
    - If using SLURM, it delegates the submission to the SLURM-specific plotter submission function.

    Args:
        exp (object): An experiment object containing the necessary attributes, such as 'hpc',
                      to determine the appropriate submission method.
    """
    if exp.hpc == 'LOCAL':
        from utility.helper_local import submit_run_plotters_local
        submit_run_plotters_local(exp)
    else:
        from utility.helper_slurm import submit_run_plotters_slurm
        submit_run_plotters_slurm(exp)

def check_exp_input_parameters(exp):
    """
    Validates the input parameters and experiment configuration.

    This function performs the following checks:
    1. Verifies that the 'agebins' parameter contains all age groups referenced in 'age_groups_aggregates'.
    2. Ensures that 'agebins' includes both the values 2 and 10.
    3. Confirms that the 'seasonality' parameter contains no more than two seasonality patterns.

    Args:
        exp (object): An experiment object containing the attributes 'age_groups_aggregates', 'agebins', and 'seasonality'.

    Raises:
        ValueError: If any of the validation checks fail, an error is raised with a descriptive message indicating the issue.
    """

    # Check agebins against age_groups_aggregates
    missing_agebins  = {age for interval in exp.age_groups_aggregates for age in interval if age != 0 and age not in exp.agebins}
    if len(missing_agebins ) > 0:
        raise ValueError(
            f"The 'agebins' parameter is not granular enough to allow aggregation by 'age_groups_aggregates'. "
            f"The following age groups are missing from 'agebins': {missing_agebins}. Please ensure they are included."
        )

    # Ensure agebins contain required values
    if 2 not in exp.agebins or 10 not in exp.agebins:
        raise ValueError(
            f"The 'agebins' parameter must include both 2 and 10. Current 'agebins' values are {exp.agebins}. "
            "Please include both values to meet the framework's requirements."
        )

    # Check that only two seasonality patterns are specified
    if len(exp.seasonality) > 2:
        raise ValueError(
            f"Only two seasonality patterns are allowed, but {len(exp.seasonality)} were specified. "
            "Please limit the number of seasonality patterns to two."
        )
    
def check_exp_inputs_emod(exp):
    """
    Checks input parameter compatibility with the framework configurations for EMOD.

    This function performs the following checks:
    1. Ensures that only a single seed is specified for EMOD burn-in simulations.
    2. Issues a warning if the burn-in period is less than 100 years, which may lead to inaccurate results.
    3. Issues a warning if the population size is below 1000, which may lead to inaccurate results.
    4. Issues a warning if the population size exceeds 10000, which may cause computational or memory issues.

    Args:
        exp (object): An experiment object containing the attributes 'emod_step', 'num_seeds_burnin',
                      'emod_burnin', 'emod_pop_size', and 'models_to_run'.

    Raises:
        ValueError: If the 'num_seeds_burnin' is not set to 1 during an EMOD burn-in simulation.
    """

    if exp.hpc == 'LOCAL':
        raise ValueError("Local execution of the framework is not functional for EMOD.")


    if exp.emod_step:
        if exp.num_seeds_burnin != 1:
            raise ValueError(
                "The current framework supports only a single seed for EMOD burn-in simulations. "
                "Please set 'num_seeds_burnin' to 1 to proceed."
            )

    if exp.emod_burnin < 100 and (
            ('EMOD' in exp.models_to_run and exp.emod_step != 'pickup') or
            'EMOD' not in exp.models_to_run ):
        print(
            f"Warning: A burn-in period of at least 100 years is recommended for EMOD. "
            f"Currently, a shorter burn-in of {exp.emod_burnin} years has been configured, which may lead to inaccurate results."
        )

    if exp.emod_pop_size < 1000:
        print(
            f"Warning: A population of at least 1000 is recommended for EMOD. "
            f"Current pop_size {exp.emod_pop_size}  may lead to inaccurate results."
        )

    if exp.emod_pop_size > 10000:
        print(
            f"Warning: A high population of over 10000 is causing computational challenges for EMOD"
            f"Current pop_size {exp.emod_pop_size}  may lead to memory related issues."
        )



def check_exp_inputs_openmalaria(exp):
    """
    Checks input parameter compatibility with the framework configurations for OpenMalaria.

    This function performs the following checks:
    1. Issues a warning if OpenMalaria is configured with 30-day survey steps and a 5-day analyzer, as this configuration will cause errors during post-processing.
    2. Raises a ValueError if the 'cc_step' intervention is specified with 30-day survey steps, which is incompatible.
    3. Issues a warning if the burn-in period is less than 80 years, which may lead to inaccurate results.
    4. Issues a warning if the population size is below 10000, which may lead to inaccurate results.

    Args:
        exp (object): An experiment object containing the attributes 'openmalaria_survey_step', 'analyzer_list',
                      'intervention_list', 'openmalaria_burnin', and 'openmalaria_pop_size'.

    Raises:
        ValueError: If the 'cc_step' intervention is specified with a 30-day survey step in OpenMalaria.
    """

    if exp.openmalaria_survey_step == '30d' and "5day" in exp.analyzer_list:
        print("Warning: OpenMalaria is configured with 30-day survey steps. Using a 5-day analyzer will cause errors during post-processing. Adjust your configuration to ensure compatibility.")

    if exp.openmalaria_survey_step == '30d' and "cc_step" in exp.intervention_list:
        raise ValueError("The 'cc_step' intervention requires 5-day survey steps in OpenMalaria. Please update the survey step configuration.")

    if exp.openmalaria_burnin < 80:
        print(
            f"Warning: A burn-in period of at least 80 years is recommended for OpenMalaria. "
            f"Currently, a shorter burn-in of {exp.openmalaria_burnin} years has been configured, which may lead to inaccurate results."
        )

    if exp.openmalaria_pop_size < 10000:
        print(
            f"Warning: A population of at least 10000 is recommended for OpenMalaria. "
            f"Current pop_size {exp.openmalaria_pop_size}  may lead to inaccurate results."
        )



def check_exp_inputs_malariasimulation(exp):
    """
    Checks input parameter compatibility with the framework configurations for malariasimulation

    This function performs the following checks:
    1. Raises a ValueError if the 'forced EIR' option is selected for entomology mode, as it is not supported.
    2. Issues a warning if the burn-in period is less than 80 years, which may lead to inaccurate results.
    3. Issues a warning if the population size is below 1000, which may lead to inaccurate results.

    Args:
        exp (object): An experiment object containing the attributes 'entomology_mode', 'malariasimulation_burnin',
                      and 'malariasimulation_pop_size'.

    Raises:
        ValueError: If the 'forced EIR' entomology mode is selected for MalariaSimulation.
    """

    if exp.entomology_mode == 'forced' :
        raise ValueError("The 'forced EIR' option is not supported in malariasimulation. Please select a valid entomology mode.")

    if exp.malariasimulation_burnin < 80:
        print(
            f"Warning: A burn-in period of at least 80 years is recommended for malariasimulation. "
            f"Currently, a shorter burn-in of {exp.malariasimulation_burnin} years has been configured, which may lead to inaccurate results."
        )

    if exp.malariasimulation_pop_size < 1000:
        print(
            f"Warning: A population of at least 1000 is recommended for malariasimulation. "
            f"Current pop_size {exp.malariasimulation_pop_size}  may lead to inaccurate results."
        )


