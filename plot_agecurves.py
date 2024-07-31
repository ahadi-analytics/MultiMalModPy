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


# Plots over age - requires PfPR_ClinicalIncidence_yr.csv
def age_curves(wdir, df, channel, sweepvar='modelname', facet_var='seasonality', age_groups_aggregates=None):
    """
    Parameters:
        wdir (str): Working directory where the plot will be saved.
        df (pandas dataframe): Dataframe that includes combined model results.
        channel (str): Variable representing the y-axis data to be plotted.
        sweepvar (str, optional): Variable to group the data and create multiple lines on the plot. Default is 'modelname'.
        facet_var (str, optional): Variable used to create subplots based on its unique values. Default is 'seasonality'. 
    Returns:
        None (plots are saved to disk).
    """
    if age_groups_aggregates is None:
        age_groups_aggregates = ['0-0.5', '0.5-1', '1-2', '2-5', '5-10', '10-15', '15-20', '20-100']

    if channel == 'prevalence_2to10':
        ylab = channel.replace('prevalence_2to10', '$\it{Pf}$PR$_{2-10}$ (%)')
    else:
        ylab = channel.replace('_', ' ')

    if facet_var == 'ageGroup':
        facet_var = 'output_target'
    if 'cm_clinical' not in [sweepvar, facet_var]:
        selected_cm = np.min(df.cm_clinical)
        df = df[(df.cm_clinical == selected_cm)]

    if 'seasonality' not in [sweepvar, facet_var]:
        selected_season = df['seasonality'].unique()[0]
        df = df[(df.seasonality == selected_season)]

    if 'output_target' not in [sweepvar, facet_var]:
        selected_output = np.max(df.output_target)
        df = df[(df.output_target == selected_output)]

    if 'modelname' not in [sweepvar, facet_var] and len(df['modelname'].unique()) > 1:
        raise ValueError('modelname needs to be specified in plot if results were combined for more than 1 model')
    df = df.groupby(['ageGroup', 'seed', sweepvar, facet_var])[channel].agg(np.mean).reset_index()

    firstPlot = True
    unique_facets = df[facet_var].unique()
    unique_facets = sorted(unique_facets)
    color_palette = sns.color_palette('colorblind', max(len(df[sweepvar].unique()), 4))

    nx = round(len(unique_facets) / 2)
    ny = 2
    f = 1
    fig = plt.figure(figsize=(10 * nx, 10 * ny))
    for fi in unique_facets:
        fdf = df[df[facet_var] == fi]
        fdf = fdf[fdf[channel].notnull()]
        ax = fig.add_subplot(ny, nx, f)
        f += 1
        max_ylim = []
        for i, (s, sdf) in enumerate(fdf.groupby([sweepvar])):
            color_key = color_selector(i, s)
            ylim_up = np.max(sdf[channel]) * 1.1
            if channel == 'prevalence' or channel == 'prevalence_2to10':
                ylim_up = min(ylim_up, 1)
            max_ylim.append(ylim_up)
            xmean, ymean = get_x_y(sdf, 'ageGroup', channel, channel)
            xmean = xmean['ageGroup']
            merge_df = pd.merge(left=xmean, right=ymean, on='ageGroup')
            merge_df['ageGroup'] = pd.Categorical(merge_df['ageGroup'],
                                                  age_groups_aggregates)  # FIXME returns NA for 0-5 and 0-100, perhaps wanted
            merge_df = merge_df.dropna()
            merge_df.sort_values('ageGroup', inplace=True)
            ax.plot(merge_df['ageGroup'], merge_df[channel], '-', linewidth=0.8, label=f"{s}",
                    color=color_palette[color_key])
            ax.fill_between(merge_df['ageGroup'], merge_df[f'{channel}_min'], merge_df[f'{channel}_max'], alpha=0.1,
                            color=color_palette[color_key])
        if firstPlot:
            lg = ax.legend(loc='upper left', bbox_to_anchor=(0.5, 1.2))
            firstPlot = False
        ax.set_ylim(0, max(max_ylim))
        ax.tick_params(axis='x', labelrotation=45)
        ax.set_xlabel('Age (years)')
        ax.set_ylabel(ylab)
        ax.set_title(f"{facet_var} = {fi}")
    fname = f'agecurves_{channel}_by_{sweepvar}'
    fig.savefig(os.path.join(wdir, f'{fname}.png'), bbox_extra_artists=(lg,), bbox_inches='tight')
    plt.close()


if __name__ == "__main__":
    args = parse_args()
    out_dir = args.directory
    modelname = args.modelname #  ['EMOD', 'OpenMalaria', 'MalSim']
    if isinstance(modelname, str):
        modelname = [modelname]

    file = open(os.path.join(out_dir, "exp.obj"), "rb")
    exp = pickle.load(file)
    age_groups_aggregates_sub = [x for x in exp.age_groups_aggregates if x not in ([[0, 5], [0, 100]])]
    age_groups_aggregates_sub = ["{}-{}".format(sublist[0], sublist[1]) for sublist in age_groups_aggregates_sub]

    channel_list = ['clinical_incidence', 'severe_incidence', 'prevalence', 'simulatedEIR']
    sweepvar = 'modelname'
    facet_var = 'ageGroup'

    if len(exp.output_target) > 1 & len(exp.output_target) <= 3:
        facet_var = 'output_target'
    if facet_var == 'ageGroup' and len(exp.cm_clinical) > 1:
        facet_var = 'cm_clinical'
    if facet_var == 'ageGroup' and len(exp.seasonality) > 1:
        facet_var = 'seasonality'

    df, wdir = get_output_df(out_dir, modelname)

    for channel in channel_list:
        print(f'#----- Plotting Age Curves for {channel}-----#')
        age_curves(wdir, df, channel=channel, sweepvar=sweepvar, facet_var=facet_var,
                   age_groups_aggregates=age_groups_aggregates_sub)
