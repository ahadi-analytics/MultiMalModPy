import argparse
import pickle
import os
import sys
import numpy as np
import pandas as pd
import matplotlib as mpl
import datetime
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
mpl.rcParams['pdf.fonttype'] = 3
plt.rcParams.update({'font.size': 16})
plt.rcParams.update({'font.sans-serif': "Arial"})

parent_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
sys.path.append(parent_dir)
from plotter.plot_helper import *


# Plots trends over available months, requires PfPR_ClinicalIncidence_mth.csv
def monthly_trends(fdir, df, channel, sweepvar='modelname', facet_var='output_target', agegrps=['0-100'], new_index=None):
    """
    Generate line plots for monthly trends for channel (yaxis) by sweepvar for selected age groups.
    Note, assumed single occurence per month, i.e. aggregated across years (reads in mmmpy_mth.csv)
    Parameters:
        fdir (str): Directory where the plot will be saved.
        df (pandas dataframe): Dataframe that includes combined model results.
        channel (str): Variable representing the y-axis data to be plotted.
        sweepvar (str, optional): Variable to group the data and create multiple lines on the plot. Default is 'output_target'.
        agegrp (str, optional): Age group filter for the data. Default is '0-5'.
    Returns:
        None (plots are saved to disk).
    Raises:
        ValueError: If no seasonal transmission pattern is specified in the data.
    """

    figure_vars = [channel] + [sweepvar, facet_var]
    df, caption_txt = subset_dataframe_for_plot(df, figure_vars, agegrps)

    color_palette = sns.color_palette('colorblind', max(len(df[sweepvar].unique()), 4))
    unique_facets = sorted_list(df[facet_var])
    unique_groups = sorted_list(df[sweepvar])

    nx = max(1, round(len(unique_facets)))
    ny = 2
    f = 1
    firstPlot = True
    fig = plt.figure(figsize=(10 * nx, 8 * ny))
    if new_index is None:
        new_index = list(range(1, 13))

    for fi in unique_facets:
        fdf = df[df[facet_var] == fi]
        ax = fig.add_subplot(ny, nx, f)
        ax.set_title(f'{facet_var} = {fi}')
        if facet_var == 'modelname':
            ax.set_title(fi)
        if facet_var == 'output_target':
            ax.set_title(f"{get_label(exp.output_type)} = {fi}")

        f += 1
        max_ylim = []
        for i, grp in enumerate(unique_groups):
            mdf = fdf[fdf[sweepvar] == grp]
            color_key = color_selector(i, grp)
            ylim_up = np.max(mdf[channel]) * 1.1
            if channel == 'prevalence' or channel == 'prevalence_2to10':
                ylim_up = min(ylim_up, 1)
            max_ylim.append(ylim_up)
            xmean, ymean = get_x_y(mdf, 'month', channel, channel)
            for ii, ff in ymean.iterrows():
                ymean.loc[ii, 'month'] = new_index[ii]
            xmean = xmean['month']
            merge_df = pd.merge(left=xmean, right=ymean, on='month')

            ax.plot(merge_df['month'], merge_df[channel], '-', linewidth=0.8,
                    label=f"{grp} ", color=color_palette[color_key])
            ax.fill_between(merge_df['month'], merge_df[f'{channel}_min'], merge_df[f'{channel}_max'],
                            alpha=0.1, color=color_palette[color_key])

        if firstPlot:
            lg = ax.legend(loc='upper left', bbox_to_anchor=(0, 1), title=f'{sweepvar}')
            firstPlot = False

        ax.set_ylim(0, max(max_ylim))
        # The following three lines help us accurately represent the months in the x axis.
        graphing_axis = [0] + new_index
        ax.set_xticks(np.arange(len(graphing_axis)))
        ax.set_xticklabels(graphing_axis)
        ax.set_xlim(1, 12)
        ax.set_xlabel('month')
        ax.set_ylabel(get_label(channel))

    if 'ageGroup' not in figure_vars:
        fname = f'monthly_{channel}_{agegrps[0]}_{sweepvar}_{facet_var}'
    else:
        fname = f'monthly_{channel}_{sweepvar}_{facet_var}'
    fname = clean_fname(fname, sweepvar, unique_groups, facet_var, unique_facets)
    fig.savefig(os.path.join(fdir, f'{fname}.png'), bbox_extra_artists=(lg,), bbox_inches='tight')
    plt.close()


# Plots over time - requires PfPR_ClinicalIncidence_mth.csv
def monthly_timeseries(fdir, df, channel, sweepvar='modelname', facet_var='ageGroup', agegrps=['0-100'], calendar_year=False):
    """
    Parameters:
        fdir (str): Directory where the plot will be saved.
        df (pandas dataframe): Dataframe that includes combined model results.
        channel (str): Variable representing the y-axis data to be plotted.
        sweepvar (str, optional): Variable to group the data and create multiple lines on the plot. Default is 'modelname'.
        facet_var (str, optional): Variable used to create subplots based on its unique values. Default is 'ageGroup'. (The default should change)
        agegrp (str, optional): Age group filter for the data. Default is '0-5'.
    Returns:
        None (plots are saved to disk).
    """

    figure_vars = [channel] + [sweepvar, facet_var]
    df, caption_txt = subset_dataframe_for_plot(df, figure_vars, agegrps)
    df['date'] = pd.to_datetime(df['date'])

    unique_facets = sorted_list(df[facet_var])
    unique_groups = sorted_list(df[sweepvar])
    color_palette = sns.color_palette('colorblind', max(len(df[sweepvar].unique()), 4))

    firstPlot = True
    nx = max(1, round(len(unique_facets) / 2))
    ny = 2
    f = 1
    fig = plt.figure(figsize=(10 * nx, 8 * ny))

    for fi in unique_facets:
        fdf = df[df[facet_var] == fi]
        ax = fig.add_subplot(ny, nx, f)
        ax.set_title(f"{facet_var} = {fi}")
        if facet_var == 'modelname':
            ax.set_title(fi)
        if facet_var == 'output_target':
            ax.set_title(f"{get_label(exp.output_type)} = {fi}")

        f += 1
        max_ylim = []
        for i, grp in enumerate(unique_groups):
            sdf = fdf[fdf[sweepvar] == grp]
            color_key = color_selector(i, grp)
            ylim_up = np.max(sdf[channel]) * 1.1
            if channel == 'prevalence' or channel == 'prevalence_2to10':
                ylim_up = min(ylim_up, 1)
            max_ylim.append(ylim_up)
            xmean, ymean = get_x_y(sdf, 'date', channel, channel)
            xmean = xmean['date']
            merge_df = pd.merge(left=xmean, right=ymean, on='date')
            merge_df.sort_values(by='date', inplace=True)
            ax.plot(merge_df['date'], merge_df[channel], '-', linewidth=0.8, label=f"{grp}",
                    color=color_palette[color_key])
            ax.fill_between(merge_df['date'], merge_df[f'{channel}_min'], merge_df[f'{channel}_max'], alpha=0.1,
                            color=color_palette[color_key])
        if firstPlot:
            lg = ax.legend(loc='upper left', bbox_to_anchor=(0, 1))
            firstPlot = False
        ax.set_ylabel(get_label(channel))
        ax.set_ylim(0, max(max_ylim))

        if calendar_year:
            ax.set_xlabel('Year')
            ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=6))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        else:
            ax.set_xlabel('Simulation monitoring year')
            start_year = df['date'].min().year
            ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: year_to_custom(x, start_year)))


    if 'ageGroup' not in figure_vars:
        fname = f'timeseries_monthly_{channel}_{agegrps[0]}_{sweepvar}_{facet_var}'
    else:
        fname = f'timeseries_monthly_{channel}_{sweepvar}_{facet_var}'
    fname = clean_fname(fname, sweepvar, unique_groups, facet_var, unique_facets)

    fig.savefig(os.path.join(fdir, f'{fname}.png'), bbox_extra_artists=(lg,), bbox_inches='tight')
    plt.close()


# Plots over time - requires PfPR_ClinicalIncidence_yr.csv
def annual_timeseries(fdir, df, channel, sweepvar='modelname', facet_var='seasonality', agegrps=['0-100'],  calendar_year=False):
    """
    Parameters:
        fdir (str): Directory where the plot will be saved.
        df (pandas dataframe): Dataframe that includes combined model results.
        channel (str): Variable representing the y-axis data to be plotted.
        sweepvar (str, optional): Variable to group the data and create multiple lines on the plot. Default is 'modelname'.
        facet_var (str, optional): Variable used to create subplots based on its unique values. Default is 'ageGroup'. (The default should change)
        agegrp (str, optional): Age group filter for the data. Default is '0-5'.
    Returns:
        None (plots are saved to disk).
    """

    figure_vars = [channel] + [sweepvar, facet_var]
    df, caption_txt = subset_dataframe_for_plot(df, figure_vars, agegrps)

    xlabel = 'Year'
    if not calendar_year:
        xlabel = 'Simulation monitoring year'
        df['year'] = df['year'] - df['year'].min()

    unique_facets = sorted_list(df[facet_var])
    unique_groups = sorted_list(df[sweepvar])
    color_palette = sns.color_palette('colorblind', max(len(df[sweepvar].unique()), 4))

    firstPlot = True
    nx = max(1, round(len(unique_facets) / 2))
    ny = 2
    f = 1
    fig = plt.figure(figsize=(10 * nx, 8 * ny))

    for fi in unique_facets:
        fdf = df[df[facet_var] == fi]
        ax = fig.add_subplot(ny, nx, f)
        ax.set_title(f"{facet_var} = {fi}")
        if facet_var == 'modelname':
            ax.set_title(fi)
        if facet_var == 'output_target':
            ax.set_title(f"{get_label(exp.output_type)} = {fi}")

        f += 1
        max_ylim = []

        for i, grp in enumerate(unique_groups):
            sdf = fdf[fdf[sweepvar] == grp]
            color_key = color_selector(i, grp)
            ylim_up = np.max(sdf[channel]) * 1.1
            if channel == 'prevalence' or channel == 'prevalence_2to10':
                ylim_up = min(ylim_up, 1)
            max_ylim.append(ylim_up)
            xmean, ymean = get_x_y(sdf, 'year', channel, channel)
            xmean = xmean['year']
            merge_df = pd.merge(left=xmean, right=ymean, on='year')
            merge_df.sort_values(by='year', inplace=True)
            ax.plot(merge_df['year'], merge_df[channel], '-', linewidth=0.8, label=f"{grp}",
                    color=color_palette[color_key])
            ax.fill_between(merge_df['year'], merge_df[f'{channel}_min'], merge_df[f'{channel}_max'], alpha=0.1,
                            color=color_palette[color_key])

        if firstPlot:
            lg = ax.legend(loc='upper left', bbox_to_anchor=(0, 1))
            firstPlot = False

        ax.set_ylabel(get_label(channel))
        ax.set_ylim(0, max(max_ylim))
        ax.set_xlabel(xlabel)
        ax.locator_params(axis='x', nbins=len(df['year'].unique()))

    if 'ageGroup' not in figure_vars:
        fname = f'timeseries_annual_{channel}_{agegrps[0]}_{sweepvar}_{facet_var}'
    else:
        fname = f'timeseries_annual_{channel}_{sweepvar}_{facet_var}'
    fname = clean_fname(fname, sweepvar, unique_groups, facet_var, unique_facets)

    fig.savefig(os.path.join(fdir, f'{fname}.png'), bbox_extra_artists=(lg,), bbox_inches='tight')
    plt.close()


if __name__ == "__main__":
    args = parse_args()
    wdir = args.directory
    modelname = args.modelname
    if isinstance(modelname, str):
        modelname = [modelname]

    exp = load_exp(wdir)

    ento_channel_list = ['n_total_mos_pop']
    epi_channel_list = ['simulatedEIR', 'clinical_incidence', 'severe_incidence', 'prevalence', 'prevalence_2to10']
    channel_list = epi_channel_list + ento_channel_list

    df_mth, out_dir = get_output_df(wdir, modelname, mth=True)
    df_yr, _ = get_output_df(wdir, modelname, yr=True)
    agegrps = ['0-100']

    out_dir = os.path.join(out_dir, 'plots')
    os.makedirs(out_dir, exist_ok=True)

    if not df_mth.empty:
        facet_var = 'modelname'
        sweepvar = 'output_target'
        for channel in channel_list:
            try:
                print(f'#----- Plotting the monthly trends for {channel} -----#')
                # Example if order or months should be shifted
                # new_index = [7, 8, 9, 10, 11, 12, 1, 2, 3, 4, 5, 6]
                new_index = None  # If none, use default 1-12
                monthly_trends(out_dir, df_mth, channel=channel, sweepvar=sweepvar, facet_var=facet_var, agegrps=agegrps,
                               new_index=new_index)
            except:
                print(f'{channel} not found in dataframe')

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
            monthly_timeseries(out_dir, df_mth, channel=channel, sweepvar=sweepvar, facet_var=facet_var, agegrps=agegrps)

    if not df_yr.empty:
        for channel in channel_list:
            print(f'#----- Plotting annual timeseries for {channel}-----#')
            annual_timeseries(out_dir, df_yr, channel=channel, sweepvar=sweepvar, facet_var=facet_var, agegrps=agegrps)
