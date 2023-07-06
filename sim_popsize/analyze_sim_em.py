import os
import argparse
import pickle
import datetime
import time
import pandas as pd
import numpy as np
import sys
from idmtools.entities import IAnalyzer
from idmtools.entities.simulation import Simulation

sys.path.append('../')
import manifest
from benchmark_plots import *
from EMOD.sample_plots import *
from EMOD.analyze_sim import *



if __name__ == "__main__":
    # Load additional required modules
    from idmtools.analysis.analyze_manager import AnalyzeManager
    from idmtools.core import ItemType
    from idmtools.core.platform_factory import Platform

    # Parse command line arguments
    args = parse_args()
    job_directory = args.directory
    exp_id = args.exp_id

    # Load experiment object
    file = open(os.path.join(job_directory, "exp.obj"), "rb")
    exp = pickle.load(file)

    exp_name = exp.exp_name
    # exp_tags =  exp.sweeps ## to do
    # Set name of eirchannel - current default for popsize simulations forced EIR onlt
    eirchannel = "EIR_scale_factor"

    # Define tags and simulation experiment configurations
    exp_tags = ['Run_Number', eirchannel, 'seasonality', 'cm_clinical_U5', 'x_Base_Population']  # ,'seasonality'
    start_year = exp.sim_start_year_em
    end_year = exp.end_year - 1
    monitoring_start = end_year - exp.monitoring_years
    burnin = None  # exp.burnin  ## Years burnin
    testmode = exp.testmode

    # Set location of output files
    wdir = os.path.join(exp.sim_out_dir, 'em')

    # Run analyzers
    with Platform('SLURM_LOCAL', job_directory=exp.suite_directory) as platform:

        analyzer = [AnnualAgebinPfPRAnalyzer(expt_name=exp_name,
                                             sweep_variables=exp_tags,
                                             working_dir=wdir,
                                             start_year=start_year,
                                             end_year=end_year,
                                             burnin=burnin),
                    BenchmarkAnalyzer(expt_name=exp_name,
                                      sweep_variables=exp_tags,
                                      working_dir=wdir,
                                      start_year=start_year,
                                      end_year=end_year,
                                      burnin=burnin),
                    BenchmarkAnalyzer_yr(expt_name=exp_name,
                                         sweep_variables=exp_tags,
                                         working_dir=wdir,
                                         start_year=start_year,
                                         end_year=end_year,
                                         burnin=burnin)]

        manager = AnalyzeManager(configuration={}, ids=[(exp_id, ItemType.EXPERIMENT)], analyzers=analyzer,
                                 partial_analyze_ok=True)
        manager.analyze()

        # Create sample plots if specified
        if testmode:
            sample_plot_yr(wdir, exp_tags)
