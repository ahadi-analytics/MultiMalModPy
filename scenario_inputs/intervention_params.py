
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


def cc_step_params(exp, overwrite_setup=True):
    if 'cc_step' not in exp.intervention_list:
        exp.intervention_list = exp.intervention_list + ['cc_step']

    ## Can be useful to allow storing some defaults on how we want to run a specific simulation, without modiyfing in launch_test
    ## Can also be errorprone between and pickup, default is False, tbd on how/when to use
    if overwrite_setup:
        exp.mem_increase_factor = 5.0  # scaling factor on default memory requested
        exp.pop_size = 10000
        exp.num_seeds_burnin = 1
        exp.num_seeds = 20
        exp.start_year = 1995
        exp.end_year = 2040
        exp.emod_step = 'burnin'
        exp.burnin = 80 # needs to be 80

    ## Specific model scaffolds to use
    exp.om_scaffold = "R0000GA_CC_STEP"  # defining which OpenMalaria XML scaffold to use
    exp.om_survey_step = '5d'
    exp.MalSim_script = 'malsim_benchmarking_exercise.R'  ## same file
    ## Parameters
    exp.eir = [1.5, 1.5, 3, 3, 9, 9]  # used for EMOD
    #exp.eir_scalar_emod = [2, 6, 0.5, 3, 0.1667, 0.3333] #function as intended
    exp.eir_scalar_emod = [1.815157038, 5.238426557, 0.550916521, 2.885935733, 0.190897016, 0.346508063] #if we wanted to hit our expected vector populations
    
    exp.eir_malsim = [1, 1, 3, 3, 16, 16] 
    #exp.eir_scalar_malsim = [3, 16, 0.333, 5.3333, 0.0625, 0.1875] #function as inteneded
    exp.eir_scalar_malsim = [2.207812419, 9.390881604, 0.45293703, 4.253478023, 0.106486275, 0.235101744] #if we wanted to hit expected vector populations

    exp.eir_om = [0.8, 0.8, 2.2, 2.2, 7, 7]
    #exp.eir_scalar_om = [-1.75, -7.75, 0.636, -2.182, 0.886, 0.686] # function as intended
    exp.eir_scalar_om = [-0.664988182, -2.845687535, 0.399395136, -1.309738637, 0.739968474, 0.567050581] #if we wanted to hit expected vector populations
    
    exp.eir_scalar_timestep_5day = int((73 * (exp.burnin + 5)))  # 5 Years in to the pickup time OpenMalaria
    exp.eir_scalar_timestep_daily = int(1825)  # 5 years in to the pickup time EMOD and Malsim
    exp.carrying_capacity_step = [f'10%-25%', f'10%-50%', f'25%-10%', f'25%-50%', f'50%-10%', f'50%-25%']
    exp.added_importation = [False, False, True, False, True, True]
    
    ## Analyzer and plotter  to run specific for CC step
    exp.plots_to_run = ['ccstep']
    exp.analyzer_list = ['all_age_analyzer', 'daily']
    return exp


## SMC setup
def smc_params(exp):
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
