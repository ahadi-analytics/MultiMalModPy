
## These functions are used in launch_test.py, for launch_simulations, a csv file is expected to read parameters from

def exp_params_to_update(exp):
    if not exp.intervention_list:
        print('No interventions specified')
    if 'cc_step' in exp.intervention_list:
        print('Adding parameters for cc_step')
        exp = cc_step_params(exp)
    if 'smc' in exp.intervention_list:
        print('Adding parameters for smc')
        exp = smc_params(exp)

    return exp


def cc_step_params(exp, overwrite_setup=False):
    if 'cc_step' not in exp.intervention_list:
        exp.intervention_list = exp.intervention_list + ['cc_step']


    ## Specific model scaffolds to use
    exp.om_scaffold = "R0000GA_CC_STEP"  # defining which OpenMalaria XML scaffold to use
    exp.om_survey_step = '5d'
    exp.MalSim_script = 'malsim_benchmarking_exercise.R'  ## same file
    ## Parameters
    exp.eir = [1.5, 1.5, 3, 3, 9, 9]  # used for EMOD
    exp.eir_scalar_emod = [2, 6, 0.5, 3, 0.1667, 0.3333]
    exp.eir_malsim = [1, 1, 3, 3, 16, 16]
    exp.eir_scalar_malsim = [3, 16, 0.333, 5.3333, 0.0625, 0.1875]
    exp.eir_om = [0.8, 0.8, 2.2, 2.2, 7, 7]
    # exp.eir_scalar_om = [2.5,8,0.4,3.2,0.125,0.3125] om requires negative values to increase, and values (1-x) to decrease
    exp.eir_scalar_om = [-1.75, -7.75, 0.636, -2.182, 0.886, 0.686]
    exp.eir_scalar_timestep_5day = int((73 * (exp.burnin + 5)))  # 5 Years in to the pickup time OpenMalaria
    exp.eir_scalar_timestep_daily = int(1825)  # 5 years in to the pickup time EMOD and Malsim
    exp.carrying_capacity_step = [f'10%-25%', f'10%-50%', f'25%-10%', f'25%-50%', f'50%-10%', f'50%-25%']

    ## The function could also be used to attach additional analyzer to run or plotters, if we want to break them down
    # exp.emod_analyzer = ['analyze_sim.py']
    # exp.openmalaria_analyzer = ['analyze_sim.py']
    exp.intervention_plotter = [ 'custom_plotter/cc_step_plots.py']  # not yet setup, but could be in next PR to disentangle benchmark_plots as needed

    ## Can be useful to allow storing some defaults on how we want to run a specific simulation, without modiyfing in launch_test
    ## Can also be errorprone between and pickup, default is False, tbd on how/when to use
    if overwrite_setup:
        exp.mem_increase_factor = 5.0  # scaling factor on default memory requested
        exp.pop_size = 10000
        exp.num_seeds_burnin = 1
        exp.num_seeds = 20
        exp.start_year = 1995
        exp.end_year = 2080
        exp.burnin = 80

    return exp


## Placeholder
def smc_params(exp):
    exp.smc_cov = [0]
    return (exp)
