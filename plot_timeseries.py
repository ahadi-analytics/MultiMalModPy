import argparse
import pickle
import os
import numpy as np
import pandas as pd
import matplotlib as mpl
import datetime
import seaborn as sns

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

mpl.rcParams['pdf.fonttype'] = 3
plt.rcParams.update({'font.size': 16})
plt.rcParams.update({'font.sans-serif': "Arial"})

from plot_helper import *


# Plots trends over available months, requires PfPR_ClinicalIncidence_mth.csv
def monthly_trends(wdir, df, channel, sweepvar='output_target', agegrp='0-100'):
    """
    Generate line plots for monthly trends for channel (yaxis) by sweepvar for selected age groups.
    Note, assumed single occurence per month, i.e. aggregated across years (reads in benchmark_mth.csv)
    Parameters:
        wdir (str): Working directory where the plot will be saved.
        df (pandas dataframe): Dataframe that includes combined model results.
        channel (str): Variable representing the y-axis data to be plotted.
        sweepvar (str, optional): Variable to group the data and create multiple lines on the plot. Default is 'output_target'.
        agegrp (str, optional): Age group filter for the data. Default is '0-5'.
    Returns:
        None (plots are saved to disk).
    Raises:
        ValueError: If no seasonal transmission pattern is specified in the data.
    """

    df = df[(df.ageGroup == agegrp)]
    if 'seasonal' in df.seasonality.unique():
        df = df[(df.seasonality == 'seasonal')]

    if sweepvar != 'cm_clinical':
        df = df[(df.cm_clinical == np.min(df.cm_clinical))]

    if channel == 'prevalence_2to10':
        ylab = channel.replace('prevalence_2to10', '$\it{Pf}$PR$_{2-10}$ (%)')
    else:
        ylab = channel.replace('_', ' ')
    color_palette = sns.color_palette('colorblind', max(len(df['modelname'].unique()), 4))
    nx = round(len(df[sweepvar].unique()) / 2)
    ny = 2
    f = 1
    firstPlot = True

    fig = plt.figure(figsize=(10 * nx, 8 * ny))
    new_index = [7, 8, 9, 10, 11, 12, 1, 2, 3, 4, 5,
                 6]  # To better showcase the montly trends, we present the months in this order

    for s in df[sweepvar].unique():
        sdf = df[(df[sweepvar] == s)]
        ax = fig.add_subplot(ny, nx, f)
        f += 1
        max_ylim = []
        for i, (m, mdf) in enumerate(sdf.groupby('modelname')):
            # plot mean, min and max of seeds
            color_key = color_selector(i, m)
            ylim_up = np.max(mdf[channel]) * 1.1

            if channel == 'prevalence' or channel == 'prevalence_2to10':
                ylim_up = min(ylim_up, 1)
            max_ylim.append(ylim_up)
            xmean, ymean = get_x_y(mdf, 'month', channel, channel)

            for ii, ff in ymean.iterrows():
                ymean.loc[ii, 'month'] = new_index[ii]

            xmean = xmean['month']
            merge_df = pd.merge(left=xmean, right=ymean, on='month')

            ax.plot(merge_df['month'], merge_df[channel], '-', linewidth=0.8, label=f"{m}",
                    color=color_palette[color_key])
            ax.fill_between(merge_df['month'], merge_df[f'{channel}_min'], merge_df[f'{channel}_max'], alpha=0.1,
                            color=color_palette[color_key])
            ax.title.set_text(f'{sweepvar} = {s}')

        if firstPlot:
            lg = ax.legend(loc='upper left', bbox_to_anchor=(0.5, 1.2))
            firstPlot = False
        ax.set_ylim(0, max(max_ylim))
        # The following three lines help us accurately represent the months in the x axis.
        graphing_axis = [0] + new_index
        ax.set_xticks(np.arange(len(graphing_axis)))
        ax.set_xticklabels(graphing_axis)
        ax.set_xlim(1, 12)
        ax.set_xlabel('month')
        ax.set_ylabel(ylab)

    fname = f'monthly_{channel}_by_{sweepvar}_age{agegrp}'
    fig.savefig(os.path.join(wdir, f'{fname}.png'), bbox_extra_artists=(lg,), bbox_inches='tight')
    plt.close()


# Plots over time - requires PfPR_ClinicalIncidence_mth.csv
def monthly_timeseries(wdir, df, channel, sweepvar='modelname', facet_var='ageGroup', agegrp='0-100'):
    """
    Parameters:
        wdir (str): Working directory where the plot will be saved.
        df (pandas dataframe): Dataframe that includes combined model results.
        channel (str): Variable representing the y-axis data to be plotted.
        sweepvar (str, optional): Variable to group the data and create multiple lines on the plot. Default is 'modelname'.
        facet_var (str, optional): Variable used to create subplots based on its unique values. Default is 'ageGroup'. (The default should change)
        agegrp (str, optional): Age group filter for the data. Default is '0-5'.
    Returns:
        None (plots are saved to disk).
    """

    if channel == 'prevalence_2to10':
        ylab = channel.replace('prevalence_2to10', '$\it{Pf}$PR$_{2-10}$ (%)')
    else:
        ylab = channel.replace('_', ' ')

    if facet_var != 'ageGroup' and agegrp is not None:
        df = df[(df.ageGroup == agegrp)]
    df['date'] = pd.to_datetime(df['date'])
    if agegrp is None:
        print('Warning: agegrp is set to None, it will combine all ages, please check your age aggregation')
        df = df.groupby(['date', 'seed', 'seasonality', 'cm_clinical', sweepvar, facet_var])[channel].agg(
            np.mean).reset_index()

    if 'cm_clinical' not in [sweepvar, facet_var]:
        selected_cm = np.min(df.cm_clinical)
        df = df[(df.cm_clinical == selected_cm)]

    if 'seasonality' not in [sweepvar, facet_var]:
        if 'seasonal' in df.seasonality.unique():
            selected_season = 'seasonal'
        else:
            selected_season = df['seasonality'].unique()[0]
        df = df[(df.seasonality == selected_season)]

    if 'output_target' not in [sweepvar, facet_var]:
        selected_output = np.max(df.output_target)
        df = df[(df.output_target == selected_output)]

    if 'modelname' not in [sweepvar, facet_var] and len(df['modelname'].unique()) > 1:
        raise ValueError('modelname needs to be specified in plot if results were combined for more than 1 model')

    unique_facets = df[facet_var].unique()
    unique_facets = np.sort(unique_facets)
    color_palette = sns.color_palette('colorblind', max(len(df[sweepvar].unique()), 4))
    firstPlot = True
    nx = round(len(df[facet_var].unique()) / 2)
    ny = 2
    f = 1
    fig = plt.figure(figsize=(10 * nx, 10 * ny))
    # Iterate through each facet and plot the lines for each group
    for fi in unique_facets:
        fdf = df[df[facet_var] == fi]
        ax = fig.add_subplot(ny, nx, f)
        f += 1
        max_ylim = []
        for i, (s, sdf) in enumerate(fdf.groupby([sweepvar])):
            color_key = color_selector(i, s)
            ylim_up = np.max(sdf[channel]) * 1.1
            if channel == 'prevalence' or channel == 'prevalence_2to10':
                ylim_up = min(ylim_up, 1)
            max_ylim.append(ylim_up)
            xmean, ymean = get_x_y(sdf, 'date', channel, channel)
            xmean = xmean['date']
            merge_df = pd.merge(left=xmean, right=ymean, on='date')
            merge_df.sort_values(by='date', inplace=True)
            ax.plot(merge_df['date'], merge_df[channel], '-', linewidth=0.8, label=f"{s}",
                    color=color_palette[color_key])
            ax.fill_between(merge_df['date'], merge_df[f'{channel}_min'], merge_df[f'{channel}_max'], alpha=0.1,
                            color=color_palette[color_key])
        if firstPlot:
            lg = ax.legend(loc='upper left', bbox_to_anchor=(0.5, 1.2))
            firstPlot = False
        ax.set_ylabel(ylab)
        ax.set_ylim(0, max(max_ylim))
        ax.set_xlabel('Year')
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=6))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.set_title(f"{facet_var} = {fi}")
    fname = f'timeseries_monthly_{channel}_by_{sweepvar}_age{agegrp}'
    fig.savefig(os.path.join(wdir, f'{fname}.png'), bbox_extra_artists=(lg,), bbox_inches='tight')
    plt.close()


# Plots over time - requires PfPR_ClinicalIncidence_yr.csv
def annual_timeseries(wdir, df, channel, sweepvar='modelname', facet_var='ageGroup', agegrp='0-100'):
    """
    Parameters:
        wdir (str): Working directory where the plot will be saved.
        df (pandas dataframe): Dataframe that includes combined model results.
        channel (str): Variable representing the y-axis data to be plotted.
        sweepvar (str, optional): Variable to group the data and create multiple lines on the plot. Default is 'modelname'.
        facet_var (str, optional): Variable used to create subplots based on its unique values. Default is 'ageGroup'. (The default should change)
        agegrp (str, optional): Age group filter for the data. Default is '0-5'.
    Returns:
        None (plots are saved to disk).
    """

    if channel == 'prevalence_2to10':
        ylab = channel.replace('prevalence_2to10', '$\it{Pf}$PR$_{2-10}$ (%)')
    else:
        ylab = channel.replace('_', ' ')

    if facet_var != 'ageGroup' and agegrp is not None:
        df = df[(df.ageGroup == agegrp)]
    if agegrp is None:
        print('Warning: agegrp is set to None, it will combine all ages, please check your age aggregation')
        df = df.groupby(['year', 'seed', 'seasonality', 'cm_clinical', sweepvar, facet_var])[channel].agg(
            np.mean).reset_index()

    if 'cm_clinical' not in [sweepvar, facet_var]:
        selected_cm = np.min(df.cm_clinical)
        df = df[(df.cm_clinical == selected_cm)]

    if 'seasonality' not in [sweepvar, facet_var]:
        if 'seasonal' in df.seasonality.unique():
            selected_season = 'seasonal'
        else:
            selected_season = df['seasonality'].unique()[0]
        df = df[(df.seasonality == selected_season)]

    if 'output_target' not in [sweepvar, facet_var]:
        selected_output = np.max(df.output_target)
        df = df[(df.output_target == selected_output)]

    if 'modelname' not in [sweepvar, facet_var] and len(df['modelname'].unique()) > 1:
        raise ValueError('modelname needs to be specified in plot if results were combined for more than 1 model')

    unique_facets = df[facet_var].unique()
    unique_facets = np.sort(unique_facets)

    color_palette = sns.color_palette('colorblind', max(len(df[sweepvar].unique()), 4))
    firstPlot = True
    nx = round(len(unique_facets) / 2)
    ny = 2
    f = 1
    fig = plt.figure(figsize=(10 * nx, 11 * ny))
    for fi in unique_facets:
        fdf = df[df[facet_var] == fi]
        ax = fig.add_subplot(ny, nx, f)
        f += 1
        max_ylim = []
        for i, (s, sdf) in enumerate(fdf.groupby([sweepvar])):
            color_key = color_selector(i, s)
            ylim_up = np.max(sdf[channel]) * 1.1
            if channel == 'prevalence' or channel == 'prevalence_2to10':
                ylim_up = min(ylim_up, 1)
            max_ylim.append(ylim_up)
            xmean, ymean = get_x_y(sdf, 'year', channel, channel)
            xmean = xmean['year']
            merge_df = pd.merge(left=xmean, right=ymean, on='year')
            merge_df.sort_values(by='year', inplace=True)
            ax.plot(merge_df['year'], merge_df[channel], '-', linewidth=0.8, label=f"{s}",
                    color=color_palette[color_key])
            ax.fill_between(merge_df['year'], merge_df[f'{channel}_min'], merge_df[f'{channel}_max'], alpha=0.1,
                            color=color_palette[color_key])
        if firstPlot:
            lg = ax.legend(loc='upper left', bbox_to_anchor=(0.5, 1.2))  # , title='Model'
            firstPlot = False
        ax.set_ylabel(ylab)
        ax.set_ylim(0, max(max_ylim))
        ax.set_xlabel('Year')
        ax.locator_params(axis='x', nbins=len(df['year'].unique()))
        ax.set_title(f"{facet_var} = {fi}")
    fname = f'timeseries_annual_{channel}_by_{sweepvar}_age{agegrp}'
    fig.savefig(os.path.join(wdir, f'{fname}.png'), bbox_extra_artists=(lg,), bbox_inches='tight')
    plt.close()


if __name__ == "__main__":
    #args = parse_args()
    out_dir = '/projects/b1139/emod-om/simulation_outputs/rer4177/test_sims_20240715/sims_dynamic_perennial__14_37_19'#args.directory
    modelname = ['EMOD', 'OpenMalaria', 'MalSim']#args.modelname 
    if isinstance(modelname, str):
        modelname = [modelname]
    file = open(os.path.join(out_dir, "exp.obj"), "rb")
    exp = pickle.load(file)

    ento_channel_list = ['n_total_mos_pop']
    epi_channel_list = ['simulatedEIR', 'clinical_incidence', 'severe_incidence', 'prevalence', 'prevalence_2to10']
    channel_list = epi_channel_list + ento_channel_list
    
    df_mth, wdir = get_output_df(out_dir, modelname, mth=True)
    df_yr, _ = get_output_df(out_dir, modelname, yr=True)
    agegrp = '0-100'  # 0-100  # if  agegrp is set to None, it will combine all ages, note, csv includes 0-5 and 0-100
    """
    if not df_mth.empty:
        sweepvar = 'output_target'
        for channel in channel_list:
            try:
                print(f'#----- Plotting the monthly trends for {channel} -----#')
                monthly_trends(wdir, df_mth, channel=channel, sweepvar=sweepvar, agegrp=agegrp)
            except:
                print(f'{channel} not found in dataframe')
    """
    sweepvar = 'modelname'
    facet_var = 'ageGroup'

    if len(exp.output_target) > 1 & len(exp.output_target) <= 3:
        facet_var = 'output_target'
    if facet_var == 'ageGroup' and len(exp.cm_clinical) > 1:
        facet_var = 'cm_clinical'
    if facet_var == 'ageGroup' and len(exp.seasonality) > 1:
        facet_var = 'seasonality'

    if not df_mth.empty:
        for channel in channel_list:
            print(f'#----- Plotting monthly timeseries for {channel}-----#')
            monthly_timeseries(wdir, df_mth, channel=channel, sweepvar=sweepvar, facet_var=facet_var, agegrp=agegrp)

    if not df_yr.empty:
        for channel in channel_list:
            print(f'#----- Plotting annual timeseries for {channel}-----#')
            annual_timeseries(wdir, df_yr, channel=channel, sweepvar=sweepvar, facet_var=facet_var, agegrp=agegrp)
