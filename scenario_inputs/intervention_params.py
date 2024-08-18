import os
import pandas as pd
import numpy as np
## These functions are used in launch_sim.py, for launch_simulations, a csv file is expected to read parameters from

def exp_params_to_update(exp):
    """
    This function sets up the exp object to add all user inputted interventions currently implemented in the framework.
    """
    if not exp.intervention_list:
        print('No interventions specified')
    if 'cc_step' in exp.intervention_list:
        print('Adding parameters for cc_step')
        exp = cc_step_params(exp)
    if 'smc' in exp.intervention_list:
        print('Adding parameters for smc')
        exp = smc_params(exp)

    return exp


def cc_step_params(exp, overwrite_setup=True):
    """
    This function sets up the exp object so that the carrying capacity perterbation can occur.

    Parameters:
        exp: Experiment object.
        overwrite_setup: bool, optional
            Flag to indicate whether to overwrite default setup parameters. Default is True.
    Returns:
        Experiment object
            An object with updated experiment parameters.
    """
    if 'cc_step' not in exp.intervention_list:
        exp.intervention_list = exp.intervention_list + ['cc_step']
    ## Can be useful to allow storing some defaults on how we want to run a specific simulation, without modiyfing in launch_test
    ## Can also be errorprone between and pickup, default is False, tbd on how/when to use
    if overwrite_setup: # FIXME - remove ?, i.e. when running a test for cc step..
        exp.mem_increase_factor = 12.0  # scaling factor on default memory requested
        exp.pop_size = 10000
        exp.num_seeds_burnin = 1
        exp.num_seeds = 20
        exp.start_year = 1995
        exp.end_year = 2040
        exp.burnin = 80

    if exp.output_type != 'prevalence_2to10':
        print("Notice: for cc_step, the output_type must be prevalence_2to10")
        exp.output_type = 'prevalence_2to10'
    print(f'Reminder: Importation is currently set to {exp.importation_rate}')
    exp.output_target = [0.1,0.25,0.5]
    exp.cc_change  = exp.output_target
    exp.step_in_years = 5
        
    ## Specific model scaffolds to use
    exp.om_scaffold = "R0000GA_CC_STEP"  # defining which OpenMalaria XML scaffold to use
    exp.om_survey_step = '5d'
    exp.MalSim_script = 'malsim_benchmarking_exercise.R'  ## same file
    ## Parameters
    exp.cc_timestep_om = int((73 * (exp.burnin + exp.step_in_years)))  # 5 Years in to the pickup time OpenMalaria
    if exp.emod_step == 'pickup':
        exp.cc_timestep_em = int(exp.step_in_years * 365)  # 5 years in to the pickup time EMOD and Malsim
    if exp.emod_step is None:
        exp.cc_timestep_em = int((exp.burnin + exp.step_in_years)*365)
    exp.cc_timestep_ms = int((exp.burnin + exp.step_in_years)*365)
    ## Analyzer and plotter  to run specific for CC step
    exp.sweep_list = exp.sweep_list + ['cc_change']
    exp.plots_to_run = ['ccstep']
    exp.analyzer_list = ['all_age_analyzer', 'cc_step']
    return exp

def cc_step_factor_calculator(df, exp, model):
    interp_path = os.path.join(exp.interp_path, model, exp.interp_csv)
    if not os.path.exists(interp_path):
        raise ValueError(f'interp_file not found: {interp_path}')
    data = pd.read_csv(interp_path)
    output = []
    for i, row in df.iterrows():
        idata = data[((data['cm_clinical'] == row['cm_clinical'])
                      & (data['seasonality'] == row['seasonality'])
                      & (data['modelname'] == model))]
        xt = idata['prevalence_2to10']
        yp = idata['n_total_mos_pop']
        xold = row['output_target']
        xnew = row['cc_change']

        interpolated_old = np.interp(xold, xt, yp)
        interpolated_new = np.interp(xnew, xt, yp)
        if model != 'OpenMalaria':
            interpolated_value = interpolated_new / interpolated_old
        else:
            interpolated_value = 1 - (interpolated_new / interpolated_old)
        output.append(interpolated_value)
    return output


def cc_title_function(df):
    output = []
    for i, row in df.iterrows():
        first_percent = int(float(row['output_target'])*100)
        to_percent = int(float(row['cc_change'])*100)
        title = f'{first_percent}%-{to_percent}%' 
        output.append(title)
    return output

## SMC setup

def smc_params(exp):
    """
    SMC currenyly requires a hard set of a few specific variables in exp.
    This function sets the exp variables to what they need to be in order for the simulations to run.
    
    Parameters:
        exp: Experiment object.

    Returns:
        Experiment object.
    """
    exp.start_year = 2000
    exp.end_year = 2008
    exp.num_seeds = 20
    exp.population = 10000
    exp.om_scaffold = "R0000GA_SMC"
    exp.smc_coverage = [0,0.6,0.8,1]
    exp.eir = [4, 8, 32]
    exp.agebins = [0.5,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,20,100]
    exp.sweep_list = exp.sweep_list + ['smc_coverage']
    return exp
