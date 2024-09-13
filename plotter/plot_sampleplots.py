import argparse
import pickle
import os
import numpy as np
import pandas as pd
import matplotlib as mpl

import seaborn as sns

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

mpl.rcParams['pdf.fonttype'] = 3
plt.rcParams.update({'font.size': 16})
plt.rcParams.update({'font.sans-serif': "Arial"})

from plotter.plot_helper import *


if __name__ == "__main__":
    args = parse_args()
    wdir = args.directory
    modelname = args.modelname # ['EMOD', 'OpenMalaria', 'malariasimulation']
    if isinstance(modelname, str):
        modelname = [modelname]
    file = open(os.path.join(wdir, "exp.obj"), "rb")
    exp = pickle.load(file)

    if 'EMOD' in modelname:
        from EMOD.sample_plots import *

        # Determine whether simulation ran with forced or dynamic EIR and set eirchannel
        # Define tags and channels for sample plots
        exp_tags = [x for x in exp.sweep_list if x != 'seed']  # + ['seed']
        sample_channels = ['Statistical Population', 'Births', 'Disease Deaths',
                           'New Infections', 'Newly Symptomatic', 'New Clinical Cases', 'New Severe Cases',
                           'Fever Prevalence', 'True Prevalence', 'PCR Gametocyte Prevalence',
                           'PCR Parasite Prevalence', 'Blood Smear Parasite Prevalence', 'PfHRP2 Prevalence',
                           'Infectious Vectors', 'EIR']

        # Create sample plots
        out_dir = os.path.join(wdir,'em')
        all_age_sample_plot(out_dir, exp_tags, sample_channels)
        sample_plot_yr(out_dir, exp_tags)
        sample_plot_mth(out_dir, exp_tags)

    if 'OpenMalaria' in modelname:
        from OpenMalaria.sample_plots import *

        # Define tags and channels for sample plots
        exp_tags = exp.sweep_list  # [x for x in exp.sweep_list if x != 'seed']
        sample_channels = ['nHost', 'nInfect', 'nPatent', 'totalInfs', 'totalPatentInf', 'nTreatments', 'nUncomp',
                           'nSevere', 'nSeq', 'nIndDeaths',  'expectedSevere'
                           'nDirDeaths', 'inputEIR', 'simulatedEIR', 'expectedDirectDeaths']  #'expectedIndirectDeaths'

        # Create sample plots
        out_dir = os.path.join(wdir,'om')
        all_age_sample_plot(out_dir, exp_tags, sample_channels)
        sample_plot_yr(out_dir, exp_tags)
        sample_plot_mth(out_dir, exp_tags)

    if 'malariasimulation' in modelname:
        from malariasimulation.sample_plots import *

        # Determine whether simulation ran with forced or dynamic EIR and set eirchannel
        # Define tags and channels for sample plots
        # exp_tags = [x for x in exp.sweep_list if x != 'seed']  # + ['seed']
        exp_tags = ['index']
        sample_channels = ['nPopulation', 'nHost', 'prevalence',
                           'incidence', 'clinical_incidence',
                           'severe_incidence', 'prevalence_2to10', 'EIR_gamb']

        # Create sample plots
        wdir = os.path.join(wdir, 'malariasimulation')
        all_age_sample_plot(wdir, exp_tags, sample_channels)
        sample_plot_yr(wdir, exp_tags)
        sample_plot_mth(wdir, exp_tags)
