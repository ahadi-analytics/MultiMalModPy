import pickle
import os
import sys
import math
import datetime
import numpy as np
import pandas as pd
import argparse

sys.path.append('../')
from OpenMalaria.measures import mm, mmi
from OpenMalaria.sample_plots import *
from benchmark_plots import *
from OpenMalaria.analyze_sim import *



if __name__ == "__main__":
    # Parse command line arguments
    args = parse_args()
    job_directory = args.directory

    # Load experiment object
    file = open(os.path.join(job_directory, "exp.obj"), "rb")
    exp = pickle.load(file)
    start_year = exp.sim_start_year_om
    wdir = os.path.join(exp.sim_out_dir, 'om')
    create_sampleplots = True

    # Determine survey step size
    if exp.om_survey_step == '30d':
        survey_steps =30
    if exp.om_survey_step == '1y':
        survey_steps =365

    # Run analyzers
    #InputEIRAnalyzer(exp, mm, start_year=start_year, survey_step_days=survey_steps)
    BenchmarkAnalyzer(exp, mmi, survey_step_days=survey_steps)
    AnnualBenchmarkAnalyzer(exp, mmi, start_year=start_year, survey_step_days=survey_steps)
    AnnualAgebinAnalyzer(exp, mm, start_year=start_year, survey_step_days=survey_steps)

    # Define tags and channels for sample plots
    exp_tags = ['seed', 'eir', 'access', 'seasonality']  # FIXME dont hardcode
    channels_inset_chart = ['nHost', 'nInfect', 'nPatent', 'totalInfs', 'totalPatentInf', 'nTreatments', 'nUncomp',
                            'nSevere', 'nSeq', 'nIndDeaths',
                            'nDirDeaths', 'inputEIR', 'simulatedEIR', 'expectedDirectDeaths',
                            'expectedSevere']  # 'expectedIndirectDeaths',

    # Create sample plots if specified
    if create_sampleplots:
        sample_plot_yr(wdir, exp_tags)

