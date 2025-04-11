import os
import pandas as pd
import numpy as np
# (Custom) Mass Drug Administration

def mda_params(exp):
    """
    This function sets up the exp object so that the carrying capacity perterbation can occur.

    Parameters:
        exp: Experiment object.

    Returns:
        Experiment object
            An object with updated experiment parameters.
    """
        
    exp.mda_in_years = 5 # determines after x amount of years, when the carrying capacity change occurs
    exp.mda_coverage = [0.8]
    #exp.mda_duration = 1 #should be in multiples of five

    if exp.emod_step is None:
        ## if None, no serialization done, hence burnin period is added to the mda_in_years
        exp.mda_timestep_EMOD = int((exp.emod_burnin + exp.mda_in_years) * 365)
    else:
        # 5 years in to the pickup time EMOD and malariasimulation, this parameter can already be defined in burnin for the respective pickup run
        exp.mda_timestep_EMOD = int(exp.mda_in_years * 365)
    
    exp.mda_timestep_malariasimulation = int((exp.malariasimulation_burnin + exp.mda_in_years) * 365)

    # 5 Years in to the pickup time OpenMalaria
    exp.openmalaria_survey_step = '5d'
    exp.mda_timestep_OpenMalaria = int((73 * (exp.openmalaria_burnin + exp.mda_in_years)))
    
    if 'mda_coverage' not in exp.plots_to_run:
        exp.plots_to_run = exp.plots_to_run + ['mda']
    if 'mda_coverage' not in exp.analyzer_list:
        exp.analyzer_list = exp.analyzer_list + ['mda']
    if 'mda_coverage' not in exp.sweep_list:
        exp.sweep_list = exp.sweep_list + ['mda_coverage']

    # Flexible parameters depending on type of run and user-specifications
    if exp.run_mode == 'production':
        print('Warning: Running MDA in production mode with pre-defined not user-defined parameters')
        exp.mem_increase_factor = 6.0  # scaling factor on default memory requested
        exp.start_year = 1995
        exp.end_year = 2010
        exp.emod_memory_per_sim = 6
        exp.emod_time_per_sim = '2:30:00'
        exp.malariasimulation_memory_per_sim = 6
        exp.malariasimulation_time_per_sim = '2:00:00'
        exp.openmalaria_memory_per_sim = 6
        exp.openmalaria_time_per_sim = '2:00:00'
    return exp


def mda_columns(exp, df):
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
            df[f'mda_timestep_{model}'] = getattr(exp, f'mda_timestep_{model}')
    return df  # TODO can be moved to postprocessing


def mda_input_check(exp):
    if exp.entomology_mode != "dynamic":
        raise ValueError(f'Invalid entomology_mode for MDA {exp.entomology_mode} specified, "dynamic" required')
    if exp.end_year - exp.start_year < exp.mda_in_years:
        raise ValueError(f"mda ({exp.mda_in_years} years) falls outside of the range of {exp.start_year} and {exp.end_year}")