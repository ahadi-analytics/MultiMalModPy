import argparse
import pickle
import os
import numpy as np
import pandas as pd
import matplotlib as mpl

import seaborn as sns
import colorcet as cc

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

mpl.rcParams['pdf.fonttype'] = 42
plt.rcParams.update({'font.size':20})
plt.rcParams.update({'font.sans-serif':"Arial"})


def parse_args():
    description = "Simulation specifications"
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "-d",
        "--directory",
        type=str,
        required=True,
        help="Job Directory where exp.obj is located",
    )
    parser.add_argument(
        "-m",
        "--emodom",
        nargs='+',
        type=str,
        required=False,
        help="Name of models to compare",
        default=['EMOD', 'OpenMalaria','MalSim']
    )

    return parser.parse_args()

def custom_sort_key(age_group):
    return int(age_group.split('-')[0])

def get_emodom_df(wdir, emodom, mth=False, timeseries=False):
    """
    Load and combine data from the specified EMOD and/or OpenMalaria benchmark output files.
    Parameters:
        wdir (str): Working directory where the data files are located.
        emodom (str or list of str): Name of models for which result CSVs should be loaded, case sensitive.
        mth (bool, optional): Set to True if the data files have monthly data. Default is False.
        timeseries (bool, optional): Set to True if the unaggregated timeseries data should be read in. Default is False
    Returns:
        df (DataFrame): Combined DataFrame containing the combined data for the models listed in emodom.
        wdir (str): Updated working directory (if applicable).
    Raises:
        ValueError: If invalid emodom value is specified.
    """
    fname = 'Benchmark.csv'
    if mth:
        fname = 'Benchmark_mth.csv'
    if timeseries:
        fname = 'PfPR_ClinicalIncidence_yr.csv'
        if mth:
            fname = 'PfPR_ClinicalIncidence_mth.csv'

    if 'OpenMalaria' in emodom:
        om_df = pd.read_csv((os.path.join(wdir, f'om/{fname}')))
        om_df['emodom'] = 'OpenMalaria'
    if 'EMOD' in emodom:
        em_df = pd.read_csv((os.path.join(wdir, f'em/{fname}')))
        em_df['emodom'] = 'EMOD'
        #This will later be replaced with the actual values of simulated EIR
        em_df['simulatedEIR'] = em_df['eir']
    if 'MalSim' in emodom:
        ms_df = pd.read_csv((os.path.join(wdir, f'MalSim/{fname}')))
        ms_df['emodom'] = 'MalSim' 
        #This will later be replaced with the actual values of simulated EIR
        ms_df['simulatedEIR'] = ms_df['eir'] 
        ms_df['inputEIR'] = ms_df['eir']   
                                   
    if 'EMOD' in emodom and 'OpenMalaria' in emodom and 'MalSim' in emodom:
        df = pd.concat([em_df, om_df])
        df = pd.concat([df, ms_df])
    elif 'OpenMalaria' in emodom and 'EMOD' in emodom and 'MalSim' not in emodom:
        df = pd.concat([em_df,om_df])
    elif 'OpenMalaria' in emodom and 'MalSim' in emodom and 'EMOD' not in emodom:
        df = pd.concat([ms_df, om_df])
    elif 'EMOD' in emodom and 'MalSim' in emodom and 'OpenMalaria' not in emodom:
        df = pd.concat([em_df, ms_df])
    elif 'OpenMalaria' and 'EMOD' not in emodom and 'MalSim' not in emodom:
        wdir = os.path.join(wdir, 'om')
        df = om_df
    elif 'EMOD' and 'OpenMalaria' not in emodom and 'MalSim' not in emodom:
        wdir = os.path.join(wdir, 'em')
        df = em_df
    elif 'MalSim' and 'OpenMalaria' not in emodom and 'EMOD' not in emodom:
        wdir = os.path.join(wdir, 'MalSim')
        df = ms_df
    else:
        raise ValueError(f"Please specify emodom as some combination of EMOD, OpenMalaria, and MalSim (list), {emodom} not valid")

    if 'ageGroup' in df.columns:
        try:
            age_grps = sorted(list(df['ageGroup'].unique()), key=custom_sort_key)
        except:
            age_grps = list(df['ageGroup'].unique())
        df['ageGroup'] = df['ageGroup'].astype('category')
        df['ageGroup'] = df['ageGroup'].cat.reorder_categories(age_grps)

    return df, wdir

def get_ysumstats(df, grpvar, channel, use_std = False):
    ymean = df.groupby(grpvar)[channel].agg(np.mean)
    ylow = df.groupby(grpvar)[channel].agg(np.min)
    yup = df.groupby(grpvar)[channel].agg(np.max)
    if use_std:
        ystd = df.groupby(grpvar)[channel].agg(np.std)
        ystd = ystd * 2
        ylow = ymean-ystd
        yup = ymean+ystd
    return [ymean, ylow, yup]

def prevalence2to10_to_incidence(wdir, emodom, channel='clinical_incidence', y_lim = 6, use_std=False):
    """
    Generates line plots for PfPR2to10 and either clinical or severe incidence per sweepvar as colors and emodom as panels.
    Parameters:
        wdir (str): Working directory where the plot will be saved.
        emodom (str or list of str): Name of models for which result dataframes should be loaded.
        channel (str): Variable representing the y-axis data to be plotted.
        sweepvar (str, optional): Variable to group the data and create multiple lines on the plot. Default is 'cm_clinical'.
    Returns:
        None (plots are saved to disk).
    """
    df, wdir = get_emodom_df(wdir, emodom)
    seasonality = list(df['seasonality'].unique())
    title = f'{channel.replace("_", " ").capitalize()}'

    if channel == 'clinical_incidence' or channel == 'severe_incidence':
        title = f'{title} (events per person per year)'

    nx = len(df['ageGroup'].unique())
    ny = len(seasonality)
    f = 1
    firstPlot = True
    fig = plt.figure(figsize=(20, 4))

    unique_groups = df['emodom'].unique()
    unique_groups = np.sort(unique_groups)
    print(unique_groups)
    num_colors = len(unique_groups)
    color_palette = sns.color_palette('husl', num_colors)

    # for each age group, plot x = prevalence 2_to_10, y = incidences
    
    for si, season in enumerate(seasonality):
        upper_ylim = -1
        for agroup in df['ageGroup'].unique():
            ax = fig.add_subplot(ny, nx, f)
            f += 1
            for mi, model in enumerate(unique_groups):
                pdf = df[(df.seasonality == season) & (df.emodom == model) & (df.ageGroup == agroup)]
                # plot mean, min and max of seeds
                xvalues = pdf.groupby('eir')['prevalence_2to10'].agg(np.mean)
                ymean, ylow, yup = get_ysumstats(pdf,'eir', channel, use_std)
                ax.plot(xvalues, ymean, label=model, color=color_palette[mi])
                ax.fill_between(xvalues, ylow, yup, alpha=0.1, color=color_palette[mi])
            ax.set_ylim(0, y_lim)
            ax.set_xlim(0, 1)
            ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1])
            ax.title.set_text(f'{agroup}')
            if firstPlot:
                lg = ax.legend(loc='upper left')  #, title='Model'
                firstPlot = False
                ax.set_ylabel(channel)
    fig.text(0.5, 0.01, '$\it{Pf}$PR$_{2-10}$ (%)', ha='center')
    if ny == 2:
        fig.text(0.98, 0.25, seasonality[1], ha='center', va='center', rotation=-90, fontsize=14)
    fname = f'pfpr2to10_to_{channel}'
    plt.tight_layout()
    
    fig.savefig(os.path.join(wdir, f'{fname}.pdf'), bbox_extra_artists=(lg,)) 


def eir_to_prevalence2to10(wdir, emodom, sweepvar='cm_clinical', eir_val='simulatedEIR', use_std=False):
    """
    Generates line plots for EIR (input or simulated) and PfPR2to10 per sweepvar as colors and emodom as panels.
    Parameters:
        wdir (str): Working directory where the plot will be saved.
        emodom (str or list of str): Name of models for which result dataframes should be loaded.
        sweepvar (str, optional): Variable to group the data and create multiple lines on the plot. Default is 'cm_clinical'.
        eir_val (str, optional): The EIR (Effective Immune Rate) value to be used for plotting. Default is 'simulatedEIR'.
    Returns:
        None (plots are saved to disk).
    """
    df, wdir = get_emodom_df(wdir, emodom)
    seasonality = list(df['seasonality'].unique())
    # caption_txt = ''

    if sweepvar != 'cm_clinical':
        # caption_txt = f'cm_clinical: {np.min(df.cm_clinical)}'
        df = df[(df.cm_clinical == np.min(df.cm_clinical))]
    
    unique_groups = df['emodom'].unique()
    num_colors = len(unique_groups)
    color_palette = sns.color_palette('husl', num_colors)
    firstPlot = True
    nx = 1
    ny = len(seasonality)
    f = 1
    fig = plt.figure(figsize=(10, 6))
    for si, season in enumerate(seasonality):
        ax = fig.add_subplot(ny, nx, f)
        f += 1
        sdf = df[(df.seasonality == season)]
        for i, (p, pdf) in enumerate(sdf.groupby([sweepvar])):
            # plot mean, min and max of seeds and age groups
            xmean = pdf.groupby('eir')[eir_val].agg(np.mean)
            ymean, ylow, yup = get_ysumstats(pdf, 'eir', 'prevalence_2to10', use_std)
            ax.plot(xmean, ymean, '-', linewidth=0.8, label=f"{p}", color=color_palette[i])
            ax.fill_between(xmean, ylow,yup, alpha=0.1,color=color_palette[i])
        if firstPlot:
            lg = ax.legend(loc='upper left')  #, title='Model'
            firstPlot = False
        ax.set_ylim(0, 1)
        ax.set_xlim(0.1, 1000)
        ax.set_xscale('symlog')
        ax.set_xlabel(f'{eir_val.replace("EIR", " annual EIR")}', fontsize=14)

    fig.text(0.02, 0.5, '$\it{Pf}$PR$_{2-10}$ (%)', ha='center', va='center', rotation='vertical', fontsize=14)
    fig.text(0.95, 0.75, seasonality[0], ha='center', va='center', rotation=-90, fontsize=14)
    if ny == 2:
        fig.text(0.95, 0.25, seasonality[1], ha='center', va='center', rotation=-90, fontsize=14)
    fig.tight_layout()

    fname = f'{eir_val}_to_pfpr2to10_by_{sweepvar}'
    fig.savefig(os.path.join(wdir, f'{fname}.pdf'), bbox_extra_artists=(lg,)) 

def input_to_simulated_eir(wdir, emodom, sweepvar='cm_clinical', use_std= False):
    """
    Generates line plots input compared to simulated EIR.
    Note, if using forced EIR, only available for OpenMalaria.
    Parameters:
        wdir (str): Working directory where the plot will be saved.
        emodom (str or list of str): Name of models for which result dataframes should be loaded.
        sweepvar (str, optional): Variable to group the data and create multiple lines on the plot. Default is 'cm_clinical'.
    Returns:
        None (plots are saved to disk).
    """
    df, wdir = get_emodom_df(wdir, emodom)
    seasonality = list(df['seasonality'].unique())
    # caption_txt = ''
    
    unique_groups = df['emodom'].unique()
    num_colors = len(unique_groups)
    color_palette = sns.color_palette('husl', num_colors)
    firstPlot = True
    
    if sweepvar != 'cm_clinical':
        # caption_txt = f'cm_clinical: {np.min(df.cm_clinical)}'
        df = df[(df.cm_clinical == np.min(df.cm_clinical))]

    nx = 1
    ny = len(seasonality)
    f = 1
    fig = plt.figure(figsize=(10, 6))
    for si, season in enumerate(seasonality):
        ax = fig.add_subplot(ny, nx, f)
        f += 1
        sdf = df[(df.seasonality == season)]
        for i, (p, pdf) in enumerate(sdf.groupby([sweepvar])):
            # plot mean, min and max of seeds and age groups
            xmean = pdf.groupby('eir')['inputEIR'].agg(np.mean)
            ymean, ylow, yup = get_ysumstats(pdf, 'eir', 'simulatedEIR', use_std)
            ax.plot(xmean, ymean, '-', linewidth=0.8, label=f"{p}",color=color_palette[i])
            ax.fill_between(xmean,ylow,yup, alpha=0.1,color=color_palette[i])
        if firstPlot:
            lg = ax.legend(loc='upper left') # , title='Model'
            firstPlot = False
        ax.set_ylim(0.1, 100000)
        ax.set_xlim(0.1, 100000)
        ax.set_yscale('symlog')
        ax.set_xscale('symlog')

    plt.xlabel('Input Annual EIR')
    plt.ylabel('Simulated Annual EIR')
    if ny == 2:
        fig.text(0.95, 0.25, seasonality[1], ha='center', va='center', rotation=-90, fontsize=14)
    fig.tight_layout()

    fname = f'input_to_simulated_eir_by_{sweepvar}'
    fig.savefig(os.path.join(wdir, f'{fname}.pdf'), bbox_extra_artists=(lg,))  


def monthly_trends(wdir, emodom, channel, sweepvar='eir', agegrp='0-5', use_std=False):
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
        ylim_up = 1
        ylab = channel.replace('prevalence_2to10', '$\it{Pf}$PR$_{2-10}$ (%)')
    elif channel == 'prevalence':
        ylim_up = 1
        ylab = channel
    elif channel == 'simulatedEIR':
        ylim_up = np.max(df[channel]) * 1.015
        ylab = channel
    else:
        ylim_up = np.max(df[channel])
        ylab = channel

    unique_groups = df['emodom'].unique()
    unique_sweep_var = df[channel].unique()
    num_colors = len(unique_groups) + len(unique_sweep_var)
    color_palette = sns.color_palette(cc.glasbey, n_colors = num_colors)
    nx = 1
    ny = len(emodom)
    f = 1
    firstPlot = True
    fig = plt.figure(figsize=(12, 12))
    for mi, model in enumerate(emodom):
        ax = fig.add_subplot(ny, nx, f)
        f += 1
        sdf = df[(df.emodom == model)]
        for i, (p, pdf) in enumerate(sdf.groupby([sweepvar])):
            # plot mean, min and max of seeds
            xmean = pdf.groupby('month')['month'].agg(np.mean)
            ymean, ylow, yup = get_ysumstats(pdf, 'month', channel, use_std)
            ax.plot(xmean, ymean, '-', linewidth=0.8, label=f"{p}", color=color_palette[i+3])
            ax.fill_between(xmean, ylow, yup, alpha=0.1,color=color_palette[i+3])
            ax.title.set_text(f'{model}')
        if firstPlot: 
            lg = ax.legend(loc='upper left', bbox_to_anchor=(1.05,1))
            firstPlot = False
        ax.set_ylim(0, ylim_up)
        ax.set_xlim(0, 12)
        ax.set_xlabel('month')
        ax.set_ylabel(ylab)
    if ny == 2:
        fig.text(0.95, 0.25, emodom[1], ha='center', va='center', rotation=-90, fontsize=14)

    fname = f'monthly_{channel}_by_{sweepvar}_age{agegrp}'
    plt.tight_layout()
    fig.savefig(os.path.join(wdir, f'{fname}.pdf'), bbox_extra_artists=(lg,), bbox_inches = 'tight')

    
    
    #fig.savefig(os.path.join(wdir, f'{fname}_legend.pdf'), bbox_extra_artists=(lg,))   


# Plots by sweeps and channels
def sweep_by_channel_plot(wdir, emodom, x_var, channel, sweepvar, facet_var, agegrp='0-5', use_std=False):
    """
    Create line plots for x_var and channel (y-axis) for different groups based on sweepvar and facet_var.
    Note, assumes time has been aggregated (i.e. benchmark.csv outcome)
    Parameters:
        wdir (str): Working directory where the plot will be saved.
        emodom (str or list of str): Name of models for which result dataframes should be loaded.
        x_var (str): Variable to be plotted on the x-axis.
        channel (str): Variable representing the y-axis data to be plotted.
        sweepvar (str): Variable to group the data and create multiple lines on the plot.
        facet_var (str): Variable used to create subplots based on its unique values.
        agegrp (str, optional): Age group filter for the data. Default is '0-5'.
    Returns:
        None (plots are saved to disk).
    """
    df, wdir = get_emodom_df(wdir, emodom, mth=False)
    if agegrp:
        df = df[(df.ageGroup == agegrp)]

    if 'cm_clinical' not in [x_var, sweepvar, facet_var]:
        df = df[(df.cm_clinical == np.min(df.cm_clinical))]

    if 'seasonality' not in [x_var, sweepvar, facet_var]:
        if 'seasonal' in df.seasonality.unique():
            df = df[(df.seasonality == 'seasonal')]

    if 'eir' not in [x_var, sweepvar, facet_var]:
        df = df[(df.eir == np.max(df.eir))]

    if 'emodom' not in [x_var, sweepvar, facet_var] and len(df['emodom'].unique()) > 1:
        raise ValueError('emodom needs to be specified in plot if results were combined for more than 1 model')

    ylim_up = np.max(df[channel])
    if channel == 'prevalence_2to10' or channel == 'prevalence':
        ylim_up = 1

    fig, axes = plt.subplots(len(df[facet_var].unique()), 1, sharex=True, figsize=(8, 5 * len(df[facet_var].unique())))

    unique_groups = df[sweepvar].unique()
    unique_facets = df[facet_var].unique()

    num_colors = len(unique_groups)
    color_palette = sns.color_palette('husl', num_colors)

    # Iterate through each facet and plot the lines for each group
    for facet_value, ax in zip (unique_facets, axes.ravel()):
        facet_data = df[df[facet_var] == facet_value]
        for p, (group_val, pdf) in enumerate(facet_data.groupby([sweepvar])):
            # plot mean, min and max of seeds
            agg_results = pdf.groupby(x_var)[channel].agg(['mean']).reset_index()
            xmean = agg_results[x_var]
            ymean, ylow, yup = get_ysumstats(pdf, x_var, channel, use_std)
            ax.plot(xmean, ymean, '-', linewidth=0.8, label=f"{group_val}", color=color_palette[p])
            ax.fill_between(xmean, ylow, yup, alpha=0.1, color=color_palette[p])
        ax.set_ylim(0, ylim_up)
        ax.set_xlabel(x_var)
        ax.set_ylabel(channel)
        ax.set_title(f"{facet_var} = {facet_value}")

    # Adjust layout to avoid overlapping
    plt.tight_layout()

    fname = f'{channel}_by_{x_var}_per_{sweepvar}_and_{facet_var}'
    fig.savefig(os.path.join(wdir, f'{fname}.pdf'))

    plt.legend(bbox_to_anchor=(1.05, 1.0), title = sweepvar, loc='upper left')
    plt.tight_layout()
    fig.savefig(os.path.join(wdir, f'{fname}_legend.pdf'))  


# Plots over time - require PfPR_ClinicalIncidence_mth.csv and PfPR_ClinicalIncidence_yr.csv
def monthly_timeseries(wdir, emodom, channel, sweepvar='emodom', facet_var='ageGroup', agegrp=None, use_std=False):
    df, wdir = get_emodom_df(wdir, emodom, mth=True, timeseries=True)
    
    df = df[(df.ageGroup == agegrp)]
    df['date'] = pd.to_datetime(df['date'])

    caption_txt = ''
    if 'cm_clinical' not in [sweepvar, facet_var]:
        selected_cm = np.min(df.cm_clinical)
        caption_txt = caption_txt + f'cm = {selected_cm}; '
        df = df[(df.cm_clinical == selected_cm)]

    if 'seasonality' not in [sweepvar, facet_var]:
        if 'seasonal' in df.seasonality.unique():
            selected_season = 'seasonal'
        else:
            selected_season = df['seasonality'].unique()[0]
        caption_txt = caption_txt + f'season = {selected_season}; '
        df = df[(df.seasonality == selected_season)]

    if 'eir' not in [sweepvar, facet_var]:
        selected_eir = np.max(df.eir)
        caption_txt = caption_txt + f'annual eir = {selected_eir}; '
        df = df[(df.eir == selected_eir)]

    if 'seasonality' not in [sweepvar, facet_var]:
        if 'seasonal' in df.seasonality.unique():
            df = df[(df.seasonality == 'seasonal')]

    if 'eir' not in [sweepvar, facet_var]:
        df = df[(df.eir == np.max(df.eir))]

    if 'emodom' not in [sweepvar, facet_var] and len(df['emodom'].unique()) > 1:
        raise ValueError('emodom needs to be specified in plot if results were combined for more than 1 model')

    fig, axes = plt.subplots(len(df[facet_var].unique()), 1, sharex=True, figsize=(8, 3 * len(df[facet_var].unique())))

    unique_groups = df[sweepvar].unique()
    
    unique_facets = df[facet_var].unique()
    unique_facets = np.sort(unique_facets)

    num_colors = len(unique_groups)
    color_palette = sns.color_palette('husl', num_colors)
    firstPlot = True
    # Iterate through each facet and plot the lines for each group
    for facet_value, ax in zip (unique_facets, axes.ravel()):
        facet_data = df[df[facet_var] == facet_value]
        upper_ylim = -1
        
        for p, (group_val, pdf) in enumerate(facet_data.groupby([sweepvar])):
            # plot mean, min and max of seeds
            agg_results = pdf.groupby('date')[channel].agg(['mean']).reset_index()
            xmean = agg_results['date']
            ymean, ylow, yup = get_ysumstats(pdf, 'date', channel, use_std)
            ax.plot(xmean, ymean, '-', linewidth=0.8, label=f"{group_val}", color=color_palette[p])
            ax.fill_between(xmean, ylow, yup, alpha=0.1, color=color_palette[p])
            if max(yup) > upper_ylim:
                upper_ylim = max(yup)
            ax.set_ylim(bottom = 0, top = max(round(upper_ylim*1.25,3),.1))
            ax.set_xlabel('Year')
            ax.set_ylabel(channel)
            ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=6))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
            ax.set_title(f"{facet_var} = {facet_value}")
        if firstPlot:
            lg = ax.legend(loc='upper left')  #, title='Model'
            firstPlot = False

    # Add caption
    plt.subplots_adjust(left=0.13, right=0.95, bottom=0.15, top=0.9, wspace=0.4, hspace=0.4)
    plt.text(0.4, -0.35, f'{caption_txt}', rotation=-0, fontsize=12)

    # Adjust layout to avoid overlapping
    # plt.tight_layout()

    fname = f'timeseries_monthly_{channel}_by_{sweepvar}_age{agegrp}'
    fig.savefig(os.path.join(wdir, f'{fname}.pdf'), bbox_extra_artists=(lg,)) 


def annual_timeseries(wdir, emodom, channel, sweepvar='emodom', facet_var='ageGroup', agegrp=None, use_std=False):
    df, wdir = get_emodom_df(wdir, emodom, mth=False, timeseries=True)
    df = df[(df.ageGroup == agegrp)]

    caption_txt = ''
    if 'cm_clinical' not in [sweepvar, facet_var]:
        selected_cm = np.min(df.cm_clinical)
        caption_txt = caption_txt + f'cm = {selected_cm}; '
        df = df[(df.cm_clinical == selected_cm)]

    if 'seasonality' not in [sweepvar, facet_var]:
        selected_season = df['seasonality'].unique()[0]
        caption_txt = caption_txt + f'season = {selected_season}; '
        df = df[(df.seasonality == selected_season)]

    if 'eir' not in [sweepvar, facet_var]:
        selected_eir = np.max(df.eir)
        caption_txt = caption_txt + f'annual eir = {selected_eir}; '
        df = df[(df.eir == selected_eir)]

    if 'emodom' not in [sweepvar, facet_var] and len(df['emodom'].unique()) > 1:
        raise ValueError('emodom needs to be specified in plot if results were combined for more than 1 model')

    fig, axes = plt.subplots(len(df[facet_var].unique()), 1, sharex=True, figsize=(8, 3 * len(df[facet_var].unique())))
    unique_groups = df[sweepvar].unique()
    unique_facets = df[facet_var].unique()
    unique_facets = np.sort(unique_facets)

    num_colors = len(unique_groups)
    color_palette = sns.color_palette('husl', num_colors)
    firstPlot = True
    for facet_value, ax in zip (unique_facets, axes.ravel()):
        facet_data = df[df[facet_var] == facet_value]
        upper_ylim = -1
        for p, (group_val, pdf) in enumerate(facet_data.groupby([sweepvar])):
            # plot mean, min and max of seeds
            agg_results = pdf.groupby('year')[channel].agg(['mean']).reset_index()
            xmean = agg_results['year']
            ymean, ylow, yup = get_ysumstats(pdf, 'year', channel, use_std)
            ax.plot(xmean, ymean, '-', linewidth=0.8, label=f"{group_val}", color=color_palette[p])
            ax.fill_between(xmean,ylow,yup, alpha=0.1, color=color_palette[p])
            if max(yup) > upper_ylim:
                upper_ylim = max(yup)
            ax.set_ylim(bottom = 0, top = max(round(upper_ylim*1.25,3),.1))
            ax.set_xlabel('Year')
            ax.set_ylabel(channel)
            ax.set_title(f"{facet_var} = {facet_value}")
        if firstPlot:
            lg = ax.legend(loc='upper left') #, title='Model'
            firstPlot = False

    # Add caption
    plt.subplots_adjust(left=0.13, right=0.95, bottom=0.15, top=0.9, wspace=0.4, hspace=0.4)
    plt.text(0.4, -0.35, f'{caption_txt}',  rotation=-0, fontsize=12)

    # Adjust layout to avoid overlapping
    #plt.tight_layout()

    fname = f'timeseries_annual_{channel}_by_{sweepvar}_age{agegrp}'
    fig.savefig(os.path.join(wdir, f'{fname}.pdf'), bbox_extra_artists=(lg,)) 

def age_curves(wdir, emodom, channel, sweepvar='emodom', facet_var='seasonality', use_std=False):
    df, wdir = get_emodom_df(wdir, emodom, mth=False, timeseries=True)
    caption_txt = ''
    if 'cm_clinical' not in [sweepvar, facet_var]:
        selected_cm = np.min(df.cm_clinical)
        caption_txt = caption_txt + f'cm = {selected_cm}; '
        df = df[(df.cm_clinical == selected_cm)]

    if 'seasonality' not in [sweepvar, facet_var]:
        selected_season = df['seasonality'].unique()[0]
        caption_txt = caption_txt + f'season = {selected_season}; '
        df = df[(df.seasonality == selected_season)]

    if 'eir' not in [sweepvar, facet_var]:
        selected_eir = np.max(df.eir)
        caption_txt = caption_txt + f'annual eir = {selected_eir}; '
        df = df[(df.eir == selected_eir)]

    if 'emodom' not in [sweepvar, facet_var] and len(df['emodom'].unique()) > 1:
        raise ValueError('emodom needs to be specified in plot if results were combined for more than 1 model')

    df = df.groupby(['ageGroup','seed',sweepvar, facet_var])[channel].agg(np.mean).reset_index()

    fig, axes = plt.subplots(len(df[facet_var].unique()), 1, sharex=True, figsize=(8, 3 * len(df[facet_var].unique())))
    firstPlot = True
    unique_groups = df[sweepvar].unique()
    unique_facets = df[facet_var].unique()
    
    num_colors = len(unique_groups)
    color_palette = sns.color_palette('husl', num_colors)
    
    for facet_value, ax in zip (unique_facets, axes.ravel()):
        facet_data = df[df[facet_var] == facet_value]
        upper_ylim = -1
        for p, (group_val, pdf) in enumerate(facet_data.groupby([sweepvar])):
            agg_results = pdf.groupby('ageGroup')[channel].agg(['mean']).reset_index()
            xmean = agg_results['ageGroup']
            ymean, ylow, yup = get_ysumstats(pdf, 'ageGroup', channel, use_std)
            if max(yup) > upper_ylim:
                upper_ylim = max(yup)
            ax.plot(xmean, ymean, '-', linewidth=0.8, label=f"{group_val}", color = color_palette[p])   
            ax.fill_between(xmean, ylow, yup, alpha=0.1, color = color_palette[p])
            ax.set_ylim(bottom = 0, top = max(round(upper_ylim*1.1,3),0.1))
            ax.set_xlabel('Age (years)')
            ax.set_ylabel(channel)
            ax.set_title(f"{facet_var} = {facet_value}")
        if firstPlot:
            lg = ax.legend(loc='upper left')  #, title='Model'
            firstPlot = False
                  

    # Add caption
    plt.subplots_adjust(left=0.13, right=0.95, bottom=0.15, top=0.9, wspace=0.4, hspace=0.4)
    plt.text(0.4, -0.35, f'{caption_txt}',  rotation=-0, fontsize=12)

    # Adjust layout to avoid overlapping
    #plt.tight_layout()

    fname = f'agecurves_{channel}_by_{sweepvar}'
    fig.savefig(os.path.join(wdir, f'{fname}.pdf'), bbox_extra_artists=(lg,)) 

def anovas(wdir, emodom):
    from scipy.stats import f_oneway
    df, wdir = get_emodom_df(wdir, emodom, mth=False, timeseries=False)
    comparisons = ['prevalence_2to10','prevalence','clinical_incidence', 'severe_incidence', 'simulatedEIR']
    emod = df[df['emodom']=='EMOD']
    malsim = df[df['emodom']=='MalSim']
    openmalaria = df[df['emodom']=='OpenMalaria']

    anova_df = pd.DataFrame(columns = ['Age Group','Objective', 'F_value', 'p_value', 'null_hyp'])
    
    #As a whole 
    for com in comparisons:
        performance_emod = emod[com]
        performance_malsim = malsim[com]
        performance_openmalaria = openmalaria[com]
        f_value, p_value = f_oneway(performance_emod, performance_malsim, performance_openmalaria)
        if p_value <= 0.05:
            null_hyp = True
        else:
            null_hyp = False
        new_row = {'Age Group': 'Across All Ages', 'Objective': com, 'F_value': f_value, 'p_value':p_value, 'null_hyp':null_hyp}
        anova_df = pd.concat([anova_df, pd.DataFrame([new_row])], ignore_index=True)
    
    #By Age Group
    for age in df['ageGroup'].unique():
        em = emod[emod['ageGroup'] == age]
        ms = malsim[malsim['ageGroup'] == age]
        om = openmalaria[openmalaria['ageGroup'] == age]
        for com in comparisons:
            performance_emod = em[com]
            performance_malsim = ms[com]
            performance_openmalaria = om[com]
            f_value, p_value = f_oneway(performance_emod, performance_malsim, performance_openmalaria)
            if p_value <= 0.05:
                null_hyp = True
            else:
                null_hyp = False
            new_row = {'Age Group': age, 'Objective': com, 'F_value': f_value, 'p_value':p_value, 'null_hyp':null_hyp}
            anova_df = pd.concat([anova_df, pd.DataFrame([new_row])], ignore_index=True)
            
    anova_df.to_csv(os.path.join(wdir,'anovas.csv'),index=False)
        
        
def rmse(wdir, emodom):
    from sklearn.metrics import mean_squared_error
    from math import sqrt
    df, wdir = get_emodom_df(wdir, emodom, mth=False, timeseries=False)
    rmse_vars = ['prevalence_2to10','prevalence','clinical_incidence', 'severe_incidence', 'simulatedEIR']
    
    rmse_df = pd.DataFrame(columns = ['Age Group','Variable', 'EMOD_TO_OPENMALARIA', 'OPENMALARIA_TO_MALSIM', 'EMOD_TO_MALSIM'] )

    for rmse_var in rmse_vars:
        group_data = df.groupby(['emodom'])[rmse_var].agg(['mean']).reset_index()
        emod_data = group_data[group_data['emodom'] == 'EMOD']
        malsim_data = group_data[group_data['emodom'] == 'MalSim']
        om_data = group_data[group_data['emodom'] == 'OpenMalaria']     
        #RMSE Between EMOD and OM
        rmse_eo = sqrt(mean_squared_error(emod_data['mean'], om_data['mean']))
        #RMSE Between OM AND MALSIM
        rmse_om = sqrt(mean_squared_error(malsim_data['mean'], om_data['mean']))
        #RMSE Between EMOD and Malsim
        rmse_em = sqrt(mean_squared_error(emod_data['mean'], malsim_data['mean']))
        #RMSE Concat
        new_row = {'Age Group': 'Across All Ages', 'Variable': rmse_var, 'EMOD_TO_OPENMALARIA': rmse_eo, 'OPENMALARIA_TO_MALSIM' : rmse_om, 'EMOD_TO_MALSIM': rmse_em}
        rmse_df = pd.concat([rmse_df, pd.DataFrame([new_row])], ignore_index =True)  
    
    for age in df['ageGroup'].unique():
        adf = df[df['ageGroup'] == age]
        for rmse_var in rmse_vars:
            group_data = adf.groupby(['emodom'])[rmse_var].agg(['mean']).reset_index()
            emod_data = group_data[group_data['emodom'] == 'EMOD']
            malsim_data = group_data[group_data['emodom'] == 'MalSim']
            om_data = group_data[group_data['emodom'] == 'OpenMalaria']     
            #RMSE Between EMOD and OM
            rmse_eo = sqrt(mean_squared_error(emod_data['mean'], om_data['mean']))
            #RMSE Between OM AND MALSIM
            rmse_om = sqrt(mean_squared_error(malsim_data['mean'], om_data['mean']))
            #RMSE Between EMOD and Malsim
            rmse_em = sqrt(mean_squared_error(emod_data['mean'], malsim_data['mean']))
            #RMSE DF
            new_row = {'Age Group': age, 'Variable': rmse_var, 'EMOD_TO_OPENMALARIA': rmse_eo, 'OPENMALARIA_TO_MALSIM' : rmse_om, 'EMOD_TO_MALSIM': rmse_em}
            rmse_df = pd.concat([rmse_df, pd.DataFrame([new_row])], ignore_index =True)
    rmse_df.to_csv(os.path.join(wdir, 'rmse.csv'),index=False)


if __name__ == "__main__":
    args = parse_args()
    job_directory = args.directory
    emodom = args.emodom
    if isinstance(emodom, str):
        emodom = [emodom]
    wdir = job_directory
    file = open(os.path.join(job_directory, "exp.obj"), "rb")
    exp = pickle.load(file)

    eir_relationship_plots = False  # reads in 'Benchmark.csv' output files
    timeseries_plots = True  # requires disaggregated result csvs (PfPR_ClinicalIncidence_<mth/yr>.csv
    sweep_plots = False  # requires customization depending on variables sweep over to plot
    if len(emodom) == 3:
        #Currently RMSE and ANOVAS are hard coded to require all three models
        print('#----- Calculating RMSE Values and ANOVAs -----#')
        rmse(wdir,emodom)
        anovas(wdir,emodom)
            
    if len(exp.eir) >= 3:
        eir_relationship_plots = True

    if eir_relationship_plots:
        print('#----- Start running pfpr-eir-incidence relationship plots -----#')
        sweepvar = 'emodom'
        eir_to_prevalence2to10(wdir, emodom, sweepvar=sweepvar, eir_val='simulatedEIR')
        # eir_to_prevalence2to10(job_directory, emodom, sweepvar=sweepvar, eir_val='inputEIR')
        input_to_simulated_eir(wdir, emodom, sweepvar=sweepvar)

        channel_list = ['clinical_incidence', 'severe_incidence', 'prevalence']
        ymaxlist = [6,0.1,1]
        for c, channel in enumerate(channel_list):
            prevalence2to10_to_incidence(wdir, emodom, channel=channel, y_lim=ymaxlist[c])

        if exp.om_survey_step == '30d' and exp.emod_step != 'burnin':
            channel_list = ['clinical_incidence', 'severe_incidence', 'prevalence', 'simulatedEIR', 'prevalence_2to10']
            sweepvar = 'eir'
            for channel in channel_list:
                try:
                    monthly_trends(wdir, emodom, channel=channel, sweepvar=sweepvar)
                except:
                    print(f'{channel} not found in dataframe')

    # Additional standardized plots - timeseries
    if timeseries_plots:
        print('#----- Running timeseries_plots -----#')
        channel_list = ['clinical_incidence', 'severe_incidence', 'prevalence']  # 'simulatedEIR', 'prevalence_2to10'

        sweepvar = 'emodom'
        if len(exp.eir) <= 3:
            facet_var = 'eir'
        else:
            facet_var = 'cm_clinical'

        for channel in channel_list:
            if exp.om_survey_step == '30d' and exp.emod_step != 'burnin':
                monthly_timeseries(wdir, emodom, channel=channel, sweepvar=sweepvar, facet_var=facet_var, agegrp='5-10')
            annual_timeseries(wdir, emodom, channel=channel, sweepvar=sweepvar, facet_var=facet_var, agegrp='5-10')
            age_curves(wdir, emodom, channel=channel, sweepvar=sweepvar, facet_var=facet_var)

    # Additional standardized plots - line colors by sweep variable
    if sweep_plots:
        print('#----- Running sweep_plots -----#')
        channel_list = ['clinical_incidence', 'severe_incidence', 'prevalence', 'prevalence_2to10']  # 'simulatedEIR'
        x_var = 'cm_clinical'
        sweepvar = 'emodom'
        facet_var = 'eir'
        for channel in channel_list:
            sweep_by_channel_plot(wdir, emodom, x_var=x_var, channel=channel, sweepvar=sweepvar, facet_var=facet_var)