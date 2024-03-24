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

from plot_helper import *


if __name__ == "__main__":
    args = parse_args()
    out_dir = args.directory
    emodom = args.emodom
    # out_dir =
    # emodom = ['EMOD', 'OpenMalaria', 'MalSim']
    if isinstance(emodom, str):
        emodom = [emodom]
    file = open(os.path.join(out_dir, "exp.obj"), "rb")
    exp = pickle.load(file)

    if 'EMOD' in emodom:
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
        wdir = os.path.join(out_dir,'em')
        all_age_sample_plot(wdir, exp_tags, sample_channels)
        sample_plot_yr(wdir, exp_tags)
        sample_plot_mth(wdir, exp_tags)

    if 'OpenMalaria' in emodom:
        from OpenMalaria.sample_plots import *

        # Define tags and channels for sample plots
        exp_tags = exp.sweep_list  # [x for x in exp.sweep_list if x != 'seed']
        sample_channels = ['nHost', 'nInfect', 'nPatent', 'totalInfs', 'totalPatentInf', 'nTreatments', 'nUncomp',
                           'nSevere', 'nSeq', 'nIndDeaths',
                           'nDirDeaths', 'inputEIR', 'simulatedEIR', 'expectedDirectDeaths',
                           'expectedSevere']  # 'expectedIndirectDeaths',

        # Create sample plots
        wdir = os.path.join(out_dir,'om')
        all_age_sample_plot(wdir, exp_tags, sample_channels)
        sample_plot_yr(wdir, exp_tags)
        sample_plot_mth(wdir, exp_tags)

    if 'MalSim' in emodom:
        from MalSim.sample_plots import *

        # Determine whether simulation ran with forced or dynamic EIR and set eirchannel
        # Define tags and channels for sample plots
        # exp_tags = [x for x in exp.sweep_list if x != 'seed']  # + ['seed']
        exp_tags = ['index']
        sample_channels = ['nPopulation', 'nHost', 'prevalence',
                           'incidence', 'clinical_incidence',
                           'severe_incidence', 'prevalence_2to10', 'EIR_gamb']

        # Create sample plots
        wdir = os.path.join(out_dir,'MalSim')
        all_age_sample_plot(wdir, exp_tags, sample_channels)
        sample_plot_yr(wdir, exp_tags)
        sample_plot_mth(wdir, exp_tags)
