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


# Plots trends over available months, requires Benchmark_mth.csv
def monthly_trends(wdir, emodom, channel, sweepvar='eir', agegrp='0-5'):
    """
    Generate line plots for monthly trends for channel (yaxis) by sweepvar for selected age groups.
    Note, assumed single occurence per month, i.e. aggregated across years (reads in benchmark_mth.csv)
    Parameters:
        wdir (str): Working directory where the plot will be saved.
        emodom (str or list of str): Name of models for which result dataframes should be loaded.
        channel (str): Variable representing the y-axis data to be plotted.
        sweepvar (str, optional): Variable to group the data and create multiple lines on the plot. Default is 'eir'.
        agegrp (str, optional): Age group filter for the data. Default is '0-5'.
    Returns:
        None (plots are saved to disk).
    Raises:
        ValueError: If no seasonal transmission pattern is specified in the data.
    """
    df, wdir = get_emodom_df(wdir, emodom, mth=True)
    df = df[(df.ageGroup == agegrp)]
    if 'seasonal' in df.seasonality.unique():
        df = df[(df.seasonality == 'seasonal')]

    if sweepvar != 'cm_clinical':
        df = df[(df.cm_clinical == np.min(df.cm_clinical))]

    if channel == 'prevalence_2to10':
        ylab = channel.replace('prevalence_2to10', '$\it{Pf}$PR$_{2-10}$ (%)')
    else:
        ylab = channel.replace('_', ' ')
    color_palette = sns.color_palette('Dark2', len(df['emodom'].unique()))
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
        for i, (m, mdf) in enumerate(sdf.groupby('emodom')):
            # plot mean, min and max of seeds
            ylim_up = np.max(mdf[channel]) * 1.1
            if channel == 'prevalence' or channel == 'prevalence_2to10':
                ylim_up = min(ylim_up, 1)
            max_ylim.append(ylim_up)
            xmean, ymean = get_x_y(mdf, 'month', channel, channel)
            for ii, ff in ymean.iterrows():
                ymean.loc[ii, 'month'] = new_index[ii]
            xmean = xmean['month']
            merge_df = pd.merge(left=xmean, right=ymean, on='month')
            ax.plot(merge_df['month'], merge_df[channel], '-', linewidth=0.8, label=f"{m}", color=color_palette[i])
            ax.fill_between(merge_df['month'], merge_df[f'{channel}_min'], merge_df[f'{channel}_max'], alpha=0.1,
                            color=color_palette[i])
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
def monthly_timeseries(wdir, emodom, channel, sweepvar='emodom', facet_var='ageGroup', agegrp='5-10'):
    """
    Parameters:
        wdir (str): Working directory where the plot will be saved.
        emodom (str or list of str): Name of models for which result dataframes should be loaded.
        channel (str): Variable representing the y-axis data to be plotted.
        sweepvar (str, optional): Variable to group the data and create multiple lines on the plot. Default is 'eir'.
        facet_var (str, optional): Variable used to create subplots based on its unique values. Default is 'ageGroup'. (The default should change)
        agegrp (str, optional): Age group filter for the data. Default is '5-10'.
    Returns:
        None (plots are saved to disk).
    """
    df, wdir = get_emodom_df(wdir, emodom, mth=True)

    if channel == 'prevalence_2to10':
        ylab = channel.replace('prevalence_2to10', '$\it{Pf}$PR$_{2-10}$ (%)')
    else:
        ylab = channel.replace('_', ' ')

    if facet_var != 'ageGroup' and agegrp is not None:
        df = df[(df.ageGroup == agegrp)]
    df['date'] = pd.to_datetime(df['date'])
    if agegrp is None:
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

    if 'eir' not in [sweepvar, facet_var]:
        selected_eir = np.max(df.eir)
        df = df[(df.eir == selected_eir)]

    if 'emodom' not in [sweepvar, facet_var] and len(df['emodom'].unique()) > 1:
        raise ValueError('emodom needs to be specified in plot if results were combined for more than 1 model')

    unique_facets = df[facet_var].unique()
    unique_facets = np.sort(unique_facets)
    color_palette = sns.color_palette('Dark2', len(df[sweepvar].unique()))
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
            ylim_up = np.max(sdf[channel]) * 1.1
            if channel == 'prevalence' or channel == 'prevalence_2to10':
                ylim_up = min(ylim_up, 1)
            max_ylim.append(ylim_up)
            xmean, ymean = get_x_y(sdf, 'date', channel, channel)
            xmean = xmean['date']
            merge_df = pd.merge(left=xmean, right=ymean, on='date')
            merge_df.sort_values(by='date', inplace=True)
            ax.plot(merge_df['date'], merge_df[channel], '-', linewidth=0.8, label=f"{s}", color=color_palette[i])
            ax.fill_between(merge_df['date'], merge_df[f'{channel}_min'], merge_df[f'{channel}_max'], alpha=0.1,
                            color=color_palette[i])
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
def annual_timeseries(wdir, emodom, channel, sweepvar='emodom', facet_var='ageGroup', agegrp='5-10'):
    """
    Parameters:
        wdir (str): Working directory where the plot will be saved.
        emodom (str or list of str): Name of models for which result dataframes should be loaded.
        channel (str): Variable representing the y-axis data to be plotted.
        sweepvar (str, optional): Variable to group the data and create multiple lines on the plot. Default is 'eir'.
        facet_var (str, optional): Variable used to create subplots based on its unique values. Default is 'ageGroup'. (The default should change)
        agegrp (str, optional): Age group filter for the data. Default is '5-10'.
    Returns:
        None (plots are saved to disk).
    """
    df, wdir = get_emodom_df(wdir, emodom, yr=True)

    if channel == 'prevalence_2to10':
        ylab = channel.replace('prevalence_2to10', '$\it{Pf}$PR$_{2-10}$ (%)')
    else:
        ylab = channel.replace('_', ' ')

    if facet_var != 'ageGroup' and agegrp is not None:
        df = df[(df.ageGroup == agegrp)]
    if agegrp is None:
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

    if 'eir' not in [sweepvar, facet_var]:
        selected_eir = np.max(df.eir)
        df = df[(df.eir == selected_eir)]

    if 'emodom' not in [sweepvar, facet_var] and len(df['emodom'].unique()) > 1:
        raise ValueError('emodom needs to be specified in plot if results were combined for more than 1 model')

    unique_facets = df[facet_var].unique()
    unique_facets = np.sort(unique_facets)

    color_palette = sns.color_palette('Dark2', len(df[sweepvar].unique()))
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
            ylim_up = np.max(sdf[channel]) * 1.1
            if channel == 'prevalence' or channel == 'prevalence_2to10':
                ylim_up = min(ylim_up, 1)
            max_ylim.append(ylim_up)
            xmean, ymean = get_x_y(sdf, 'year', channel, channel)
            xmean = xmean['year']
            merge_df = pd.merge(left=xmean, right=ymean, on='year')
            merge_df.sort_values(by='year', inplace=True)
            ax.plot(merge_df['year'], merge_df[channel], '-', linewidth=0.8, label=f"{s}", color=color_palette[i])
            ax.fill_between(merge_df['year'], merge_df[f'{channel}_min'], merge_df[f'{channel}_max'], alpha=0.1,
                            color=color_palette[i])
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
    args = parse_args()
    out_dir = args.directory
    emodom = args.emodom
    # out_dir =
    # emodom = ['EMOD', 'OpenMalaria', 'MalSim']
    if isinstance(emodom, str):
        emodom = [emodom]
    file = open(os.path.join(out_dir, "exp.obj"), "rb")
    exp = pickle.load(file)

    channel_list = ['clinical_incidence', 'severe_incidence', 'prevalence', 'simulatedEIR', 'prevalence_2to10','n_infectious_mos']
    """
    if exp.om_survey_step == '30d' and exp.emod_step != 'burnin':
        sweepvar = 'eir'
        for channel in channel_list:
            try:
                print(f'#----- Plotting the monthly trends for {channel} -----#')
                monthly_trends(out_dir, emodom, channel=channel, sweepvar=sweepvar, agegrp='0-100')  # 0-100
            except:
                print(f'{channel} not found in dataframe')
    """
    sweepvar = 'emodom'
    facet_var = 'ageGroup'

    if len(exp.eir) > 1 & len(exp.eir) <= 3:
        facet_var = 'eir'
    if facet_var == 'ageGroup' and len(exp.cm_clinical) > 1:
        facet_var = 'cm_clinical'
    if facet_var == 'ageGroup' and len(exp.seasonality) > 1:
        facet_var = 'seasonality'

    for channel in channel_list:
        if exp.om_survey_step == '30d' and exp.emod_step != 'burnin':
            print(f'#----- Plotting monthly timeseries for {channel}-----#')
            monthly_timeseries(out_dir, emodom, channel=channel, sweepvar=sweepvar, facet_var=facet_var, 
                               agegrp='0-100')  # if you set agegrp to None, it will combine all ages, note, csv includes 0-5 and 0-100
        print(f'#----- Plotting annual timeseries for {channel}-----#')
        annual_timeseries(out_dir, emodom, channel=channel, sweepvar=sweepvar, facet_var=facet_var,
                          agegrp='0-100')  # if you set agegrp to None, it will combine all ages, note, csv includes 0-5 and 0-100
