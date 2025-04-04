import argparse
import pickle
import os
import sys
import numpy as np
import pandas as pd
import matplotlib as mpl
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

mpl.rcParams['pdf.fonttype'] = 3
plt.rcParams.update({'font.size': 16})
plt.rcParams.update({'font.sans-serif': "Arial"})

parent_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
sys.path.append(parent_dir)
from plotter.plot_helper import *
from plotter.custom.example1 import *  ### Modify this import for any other custom plots to run, or add additional



if __name__ == "__main__":
    args = parse_args()
    wdir = args.directory
    modelname = args.modelname
    if isinstance(modelname, str):
        modelname = [modelname]
    file = open(os.path.join(wdir, "exp.obj"), "rb")
    exp = pickle.load(file)

    channel_list = ['prevalence_2to10']
    df, out_dir = get_output_df(wdir, modelname)
    df_mth, _ = get_output_df(wdir, modelname, mth=True)

    out_dir = os.path.join(out_dir, 'plots')
    if len(modelname) == 1 and len(exp.models_to_run) > 1:
        out_dir = os.path.join(out_dir, modelname[0])
    os.makedirs(out_dir, exist_ok=True)

    generate_plots_example1(out_dir, exp, df, df_mth)  ### Add or modify for plots to run from imported script

