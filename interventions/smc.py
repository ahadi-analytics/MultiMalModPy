# Seasonal malaria chemoprevention (SMC)


## SMC setup, currently not supported

# def smc_params(exp):
#     """
#     SMC currenyly requires a hard set of a few specific variables in exp.
#     This function sets the exp variables to what they need to be in order for the simulations to run.
#
#     Parameters:
#         exp: Experiment object.
#
#     Returns:
#         Experiment object.
#     """
#     exp.start_year = 2000
#     exp.end_year = 2008
#     exp.num_seeds = 20
#     exp.population = 10000
#     exp.openmalaria_scaffold = "R0000GA_SMC"
#     exp.smc_coverage = [0,0.6,0.8,1]
#     exp.eir = [4, 8, 32]
#     exp.agebins = [0.5,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,20,100]
#     exp.sweep_list = exp.sweep_list + ['smc_coverage']
#     return exp
