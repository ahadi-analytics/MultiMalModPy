import os
import pandas as pd
import numpy as np
import manifest
from utility.experiment import LoadExperiment

def update_exp(exp):
    """
    Generates the default simulation settings we are interested in using across all three models,
    before any interventions or other functions overwrite the items in exp.
    User, if you want to make adjustments to your simulation and you are not using the overwrite functions,
    I would recommend you make those changes here.

    Example:
        exp.seasonality = get_param(exp_scen_df, 'seasonality', listparam=True)

    Args:
        args (obj, lst): List of inputs grabbed from the parse_args function.
        manifest (file, lst): List of inputs grabbed from the manifest.py file.
            manifest's inputs are more relevant for directories and hpc settings, then simulation settings.
    Returns:
        exp (Experiment): Returns an Experiment Object with simulation and hpc settings that will get shared across
            the three models.
    """
    #exp = LoadExperiment(args, manifest)

    if exp.run_mode == None or exp.run_mode == 'test' :
        # Specify OpenMalaria XML and survey step, malariasimulation simulation setup
        # Note if, interventions are specified in intervention_list, these will get updated via get_intervention_params
        exp.openmalaria_scaffold = "R0000GA"  # defining which OpenMalaria XML scaffold to use
        exp.openmalaria_survey_step = '5d'  # '30d'
        exp.malariasimulation_script = 'malariasimulation_base.R'
        exp.analyzer_script = ['analyze_sim.py']
        exp.analyzer_list = ['all_age_analyzer', 'annual', '5day', 'monthly',
                             'timeavrg']  # ['all_age_analyzer', '5day', 'annual','monthly','timeavrg'.'daily']
        exp.plots_to_run = ['relationship', 'timeseries',
                            'agecurves']  # gets overwritten by get_intervention_params(exp) depending on 'interventions' specified

        # Flag to select whether to run with (dynamic) or without vector model (forced)
        exp.entomology_mode = 'dynamic'  # dynamic, forced
        exp.seasonality = ['perennial']  # ["perennial", "seasonal"]  #FIXME currently allowing only single seasonal pattern
        #"Current framework support only 1 seasonality patten per experiment"
        exp.mem_increase_factor = 5.0  # scaling factor on default memory requested

        # Define age groups to report/monitor in simulations and to aggregate in output
        exp.agebins = [0.5, 1, 2, 5, 10, 15, 20, 100]  # FIXME Note, keep these to ensure smooth postprocessing
        exp.age_groups_aggregates = [[0, 0.5], [0.5, 1], [1, 2], [2, 5], [5, 10], [10, 15], [15, 20], [20, 100], [0, 5],
                                     [0, 100]]

        # Define case management start and coverage
        exp.cm_start = 1
        exp.cm_clinical = [0]  # , 0.45
        exp.cm_severe = [0] # , 0.52
        #exp.cm_severe_clinical_combinations = False # Flag whether to run cm_clinical and cm_severe paramter combinations (default is pairwise  combination)
        exp.detectionLimit = 40
        exp.importation_rate = 0  # number of infections imported per 1000 population per year, i.e. suggested 0 or 5
        exp.num_seeds_burnin = 1  # used only if emod_step=='burnin' (EMOD specific)

        exp.burnin = 80  # Duration of burnin (pre-monitoring) period, should be 80 years to establish immunity in the population
        exp.start_year = 2000  # start of pickup and monitoring period (for EMOD set given burnin and serialization flags)
        exp.end_year = 2005  # end of pickup and monitoring period

        exp.pop_size = 10000
        exp.num_seeds = 3  # suggested minimum 3
        if exp.output_type == 'eir':
            exp.output_target = [1, 5, 10, 20, 50, 100, 500, 1000]
        if exp.output_type == 'prevalence_2to10':
            exp.output_target = [0.05,0.1,0.2,0.25,0.4,0.45,0.5,0.6,0.7,0.8]

        # Name of parameters to vary
        exp.sweep_list = ['output_target', 'cm_clinical', 'seasonality']


    return (exp)


