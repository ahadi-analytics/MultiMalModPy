import os
import pandas as pd
import numpy as np
# (Custom) Mass Drug Administration

def infcl_params(exp):
    """
    This function sets up the exp object so that the infectious clearance perterbation can occur.

    Parameters:
        exp: Experiment object.

    Returns:
        Experiment object
            An object with updated experiment parameters.
    """
        
    exp.infcl_in_years = 5 # determines after x amount of years, when the infectious clearance  occurs
    exp.infcl_coverage = [0.8] # infcl_coverage is a sweep variable, you can select multiple values

    if exp.emod_step is None:
        ## if None, no serialization done, hence burnin period is added to the infcl_in_years
        exp.infcl_timestep_EMOD = int((exp.emod_burnin + exp.infcl_in_years) * 365)
    else:
        # 5 years in to the pickup time EMOD and malariasimulation, this parameter can already be defined in burnin for the respective pickup run
        exp.infcl_timestep_EMOD = int(exp.infcl_in_years * 365)
    
    exp.infcl_timestep_malariasimulation = int((exp.malariasimulation_burnin + exp.infcl_in_years) * 365)

    # 5 Years in to the pickup time OpenMalaria
    exp.openmalaria_survey_step = '5d'
    exp.infcl_timestep_OpenMalaria = int((73 * (exp.openmalaria_burnin + exp.infcl_in_years))-1)
    
    if 'infcl' not in exp.plots_to_run:
        exp.plots_to_run = exp.plots_to_run + ['infcl']
    if '5day' not in exp.analyzer_list:
        exp.analyzer_list = exp.analyzer_list + ['5day']
    if 'infcl_coverage' not in exp.sweep_list:
        exp.sweep_list = exp.sweep_list + ['infcl_coverage']
    if 'infcl_coverage' not in exp.intervention_analyzer_columns:
        exp.intervention_analyzer_columns = exp.intervention_analyzer_columns + ['infcl_coverage']    

    # Flexible parameters depending on type of run and user-specifications
    if exp.run_mode == 'production':
        print('Warning: Running infcl in production mode with pre-defined not user-defined parameters')
        exp.mem_increase_factor = 6.0  # scaling factor on default memory requested
        exp.start_year = 1995
        exp.end_year = 2020
        exp.emod_memory_per_sim = 6
        exp.emod_time_per_sim = '3:59:00'
        exp.malariasimulation_memory_per_sim = 6
        exp.malariasimulation_time_per_sim = '2:00:00'
        exp.openmalaria_memory_per_sim = 6
        exp.openmalaria_time_per_sim = '2:00:00'
    return exp


def infcl_columns(exp, df):
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
            df[f'infcl_timestep_{model}'] = getattr(exp, f'infcl_timestep_{model}')
    return df  # TODO can be moved to postprocessing


def infcl_input_check(exp):
    if exp.end_year - exp.start_year < exp.infcl_in_years:
        raise ValueError(f"infcl ({exp.infcl_in_years} years) falls outside of the range of {exp.start_year} and {exp.end_year}")