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

# Helps process script inputs
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
        default=['EMOD', 'OpenMalaria', 'MalSim']
    )

    return parser.parse_args()


def custom_sort_key(age_group):
    return int(age_group.split('-')[0])


# Creates the combined dataframes for all models simulated.
def get_emodom_df(wdir, emodom, mth=False, daily=False, timeseries=False, condensed=False):
    """
    Load and combine data from the specified EMOD and/or OpenMalaria benchmark output files.
    Parameters:
        wdir (str): Working directory where the data files are located.
        emodom (str or list of str): Name of models for which result CSVs should be loaded, case sensitive.
        mth (bool, optional): Set to True if the data files have monthly data. Default is False.
        daily (bool, optional): Set to True if the data files have daily timestep data. Default is False. If both mth and daily are true, only daily will be processed.
        timeseries (bool, optional): Set to True if the unaggregated timeseries data should be read in. Default is False
        condensed (bool, optional): Set to True, only a set list of eirs will be present in the final csv.
    Returns:
        df (DataFrame): Combined DataFrame containing the combined data for the models listed in emodom.
        wdir (str): Updated working directory (if applicable).
    Raises:
        ValueError: If invalid emodom value is specified.
    """
    cols_to_keep = None # default read all
    fname = 'Benchmark.csv'
    if mth:
        fname = 'Benchmark_mth.csv'
    if timeseries:
        fname = 'PfPR_ClinicalIncidence_yr.csv'
        if mth:
            fname = 'PfPR_ClinicalIncidence_mth.csv'
        if daily:
            fname = 'PfPR_ClinicalIncidence_daily.csv'
            cols_to_keep = ['index', 'timestep', 'ageGroup', 'simulatedEIR', 'prevalence_2to10', 'prevalence',
                            'clinical_incidence', 'severe_incidence', 'n_total_mos_pop', 'seed', 'carrying_capacity_step']

    if os.path.isfile(os.path.join(wdir, fname)):
        df = pd.read_csv((os.path.join(wdir, fname)), low_memory=False)
    else:
        if 'OpenMalaria' in emodom:
            om_df = pd.read_csv((os.path.join(wdir, f'om/{fname}')), usecols=cols_to_keep)
            om_df['emodom'] = 'OpenMalaria'

        if 'EMOD' in emodom:
            em_df = pd.read_csv((os.path.join(wdir, f'em/{fname}')), usecols=cols_to_keep)
            em_df['emodom'] = 'EMOD'
            em_df['seed'] = em_df['seed'] + 1  # increase the seed count by one to make sure seed number is consistent across models
            #em_df = em_df[em_df['eir'] >= 1]  # get rid of eirs <1 as EMOD can't sustain malaria at an eir less than 1, for pop of 10,000.

        if 'MalSim' in emodom:
            ms_df = pd.read_csv((os.path.join(wdir, f'MalSim/{fname}')), usecols=cols_to_keep)
            ms_df['emodom'] = 'MalSim'

        if 'EMOD' in emodom and 'OpenMalaria' in emodom and 'MalSim' in emodom:
            df = pd.concat([em_df, om_df])
            df = pd.concat([df, ms_df])
        elif 'OpenMalaria' in emodom and 'EMOD' in emodom and 'MalSim' not in emodom:
            df = pd.concat([em_df, om_df])
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
            raise ValueError(
                f"Please specify emodom as some combination of EMOD, OpenMalaria, and MalSim (list), {emodom} not valid")

        if 'ageGroup' in df.columns:
            try:
                age_grps = sorted(list(df['ageGroup'].unique()), key=custom_sort_key)
            except:
                age_grps = list(df['ageGroup'].unique())
            df['ageGroup'] = df['ageGroup'].astype('category')
            df['ageGroup'] = df['ageGroup'].cat.reorder_categories(age_grps)
        if condensed: #For our testing purposes, we can reduce the eir's in our simulations to the 6 we think are most useful to compare/graph together.
            eir_list = [1,5,10,50,200,1000]
            df = df[df['eir'].isin(eir_list)]
        warning_df = df[df['simulatedEIR'] == 0]
        if len(warning_df) > 0 and daily is False: #we don't want to include simulations were eir was 0 or less, because we won't get any outcome measures and that crashes the system
            print('Warning: some eirs had simulated EIRS of 0, and were removed')
            df = df[df['simulatedEIR'] > 0]
            df = df[df['simulatedEIR'].notnull()]
        if not daily:
            df.to_csv(os.path.join(wdir, fname), index=False)
    return df, wdir


# Calculates x-axis and y-axis values for each plot
def get_x_y(df, grpvar, x_channel, y_channel, use_std=False):
    """
    Load and combine data from the specified EMOD and/or OpenMalaria benchmark output files.
    Parameters:
        df (DataFrame): The Dataframe we will use to group and calculate our x and y values.
        grpvar (str): The variable in the dataframe we will group the x and y values by.
        x_channel (str): The variable that will serve as our x axis in the graph
        y_channel (str): The variable that will serve as our y axis in the graph
        use_std (bool, optional): Do you use two standard deviations for the fill (True) or percentiles (False). Default False.
    Returns:
        xmean (DataFrame): a DataFrame containing values for the x axis.
        ymean (DataFrame): a DataFrame containing values for the y axis as well as either 95% confidence interval or percentiles 2.75 to 97.25
    """
    xmean = df.groupby(grpvar)[x_channel].agg(np.mean).reset_index()
    ymean = df.groupby(grpvar)[y_channel].agg(np.mean).reset_index()
    if use_std: #TODO fix up using the standard deviation, right now it wouldn't work, but since we are moving forward with percentiles instead, maybe we just remove it.
        ystd = df.groupby(grpvar)[y_channel].agg(np.std)
        ystd = ystd * 2
        ylow = ymean - ystd
        yup = ymean + ystd
        ymean = pd.merge(left=ymean, right = ylow, on=grpvar)
        ymean = pd.merge(left=ymean, right = yup, on=grpvar)
    else:
        p_df = pd.DataFrame(columns=[grpvar,f'{y_channel}_min',f'{y_channel}_max'])
        for i, row in ymean.iterrows():
            p = df[df[grpvar]==row[grpvar]]
            pmin = np.nanpercentile(p[y_channel],2.5,axis=0)
            pmax = np.nanpercentile(p[y_channel],97.5,axis=0)
            new_row = pd.DataFrame([{grpvar: row[grpvar], f'{y_channel}_min': pmin, f'{y_channel}_max':pmax}])
            p_df = pd.concat([p_df,new_row],axis =0, ignore_index=True)
        ymean = pd.merge(left=ymean, right = p_df, on=grpvar)
    return xmean, ymean


# Plots prevalence 2 to 10 by output variable, requires benchmark.csv
def prevalence2to10_to_incidence(wdir, emodom, channel='clinical_incidence', use_std=False):
    """
    Generates line plots for PfPR2to10 and either clinical or severe incidence per sweepvar as colors and emodom as panels.
    Parameters:
        wdir (str): Working directory where the plot will be saved.
        emodom (str or list of str): Name of models for which result dataframes should be loaded.
        channel (str): Variable representing the y-axis data to be plotted.
        use_std (bool, optional): Do you use two standard deviations for the fill (True) or percentiles (False). Default False.
    Returns:
        None (plots are saved to disk).
    """
    df, wdir = get_emodom_df(wdir, emodom)
    ylab = channel.replace('_', ' ')
    seasonality = list(df['seasonality'].unique())
    nx = len(df['ageGroup'].unique())
    ny = 1
    f = 1
    firstPlot = True
    fig = plt.figure(figsize=(10*nx, 10*ny))

    unique_groups = df['emodom'].unique()
    unique_groups = np.sort(unique_groups)
    num_colors = len(unique_groups)
    color_palette = sns.color_palette('Paired', num_colors)

    # for each age group, plot x = prevalence 2_to_10, y = incidences (or prevalence)
    for si, season in enumerate(seasonality):
        sdf = df[df.seasonality == season]
        for agroup in sdf['ageGroup'].unique():
            ax = fig.add_subplot(ny, nx, f)
            f += 1
            adf = sdf[sdf.ageGroup == agroup]
            for mi, model in enumerate(unique_groups):
                pdf = adf[adf.emodom == model]
                if not pd.isnull(pdf['prevalence_2to10']).all():
                # plot mean, min and max of seeds
                    xmean, ymean = get_x_y(pdf, 'eir', 'prevalence_2to10', channel, use_std)
                    merge_df = pd.merge(left = xmean, right = ymean, on = 'eir')
                    if channel == 'simulatedEIR':
                        merge_df.sort_values(by='eir', inplace=True)
                    else:
                        merge_df.sort_values(by='prevalence_2to10', inplace=True)
                    ax.plot(merge_df['prevalence_2to10'], merge_df[channel], label=model, color=color_palette[mi])
                    ax.fill_between(merge_df['prevalence_2to10'], merge_df[f'{channel}_min'], merge_df[f'{channel}_max'], alpha=0.1, color=color_palette[mi])
            if channel == "prevalence":
                y_lim = 1
            else:
                y_lim = max(adf[channel])*1.1
            ax.set_ylim(0, y_lim)
            ax.set_xlim(0, 1)
            ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1])
            ax.title.set_text(f'{agroup}')
            ax.set_ylabel(ylab)
            ax.set_xlabel('$\it{Pf}$PR$_{2-10}$ (%)')
            if firstPlot:
                lg = ax.legend(loc='upper left', bbox_to_anchor=(0.5, 1.2))
                firstPlot = False
    fname = f'pfpr2to10_to_{channel}'
    fig.savefig(os.path.join(wdir, f'{fname}.png'), bbox_extra_artists=(lg,), bbox_inches='tight')
    plt.close()


# Plots prevalence 2 to 10 by incidence, with subplots seperated by 3 age groups. These graphs were requested by Narimane to reflect 
# figure 1 in https://www.nature.com/articles/ncomms9170
def prevalence2to10_to_incidence_by_age_and_model(wdir, emodom, channel='clinical_incidence', use_std=False):
    """
    Generates line plots for PfPR2to10 and either clinical or severe incidence as panels seperated by model (columns) and ages (rows).
    Parameters:
        wdir (str): Working directory where the plot will be saved.
        emodom (str or list of str): Name of models for which result dataframes should be loaded.
        channel (str): Variable representing the y-axis data to be plotted.
        use_std (bool, optional): Do you use two standard deviations for the fill (True) or percentiles (False). Default False.
    Returns:
        None (plots are saved to disk).
    """
    df, wdir = get_emodom_df(wdir, emodom)
    ylab = channel.replace('_', ' ')
    seasonality = list(df['seasonality'].unique())
    nx = 3
    ny = 3
    f = 1
    fig = plt.figure(figsize=(10*nx, 10*ny))

    unique_groups = df['emodom'].unique()
    unique_groups = np.sort(unique_groups)
    num_colors = len(unique_groups)
    color_palette = sns.color_palette('Paired', num_colors)
    young_child = ['0-0.5','0.5-1','1-2','2-5']
    older_child = ['5-10','10-15']
    adult = ['15-20','20-100']
    ages_list = [young_child, older_child, adult]
    mean_vars = [channel, 'prevalence_2to10']
    # for each age group, plot x = prevalence 2_to_10, y = incidences (or prevalence)
    for si, season in enumerate(seasonality):
        sdf = df[df.seasonality == season]
        for ages in ages_list:
            adf = sdf[sdf['ageGroup'].isin(ages)]
            for mi, model in enumerate(unique_groups):
                ax = fig.add_subplot(ny, nx, f)
                f += 1
                mdf = adf[adf.emodom == model]
                mdf = mdf.groupby(['seed','eir'])[mean_vars].agg(np.mean).reset_index()
                if not pd.isnull(mdf['prevalence_2to10']).all():
                # plot mean, min and max of seeds
                    xmean, ymean = get_x_y(mdf, 'eir', 'prevalence_2to10', channel, use_std)
                    merge_df = pd.merge(left = xmean, right = ymean, on = 'eir')
                    merge_df.sort_values(by='prevalence_2to10', inplace=True)
                    ax.plot(merge_df['prevalence_2to10'], merge_df[channel], label=model, color=color_palette[mi])
                    ax.fill_between(merge_df['prevalence_2to10'], merge_df[f'{channel}_min'], merge_df[f'{channel}_max'], alpha=0.1, color=color_palette[mi])
                if channel == "prevalence":
                    y_lim = 1
                else:
                    y_lim = max(adf[channel])*1.01
                ax.set_ylim(0, y_lim)
                ax.set_xlim(0, 1)
                ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1])
                ax.title.set_text(f'{model}: {ages}')
                ax.set_ylabel(ylab)
                ax.set_xlabel('$\it{Pf}$PR$_{2-10}$ (%)')
    fname = f'pfpr2to10_to_{channel}_by_age_by_model'
    fig.savefig(os.path.join(wdir, f'{fname}.png'), bbox_inches='tight')
    plt.close()

# Plots simulated eir vs output variable, requires benchmark.csv
def eir_to_outcome(wdir, emodom, sweepvar='cm_clinical', eir_val='simulatedEIR', channel = 'prevalence_2to10', use_std=False, agegrp = '0-5'):
    """
    Generates line plots for EIR (input or simulated) and a requested outcome variable per emodom as colors and sweepvar as panels.
    Parameters:
        wdir (str): Working directory where the plot will be saved.
        emodom (str or list of str): Name of models for which result dataframes should be loaded.
        sweepvar (str, optional): Variable to group the data and create multiple panels on the plot. Default is 'cm_clinical'.
        eir_val (str, optional): The EIR (entomological inoculation rate) value to be used for plotting. Default is 'simulatedEIR'.
        channel (str, optional): the outcome variable to compare to eir
        use_std (bool, optional): Do you use two standard deviations for the fill (True) or percentiles (False). Default False.
        agegrp (str, optional): Limits the resulting graphs to the selected age group. Default 0-5.
    Returns:
        None (plots are saved to disk).
    """
    df, wdir = get_emodom_df(wdir, emodom) # Grab the dataframe
    df = df[df['ageGroup'] == agegrp] # Limit the dataframe to desired age group
    seasonality = list(df['seasonality'].unique()) #Identify seasonality patterns to iterate over while graphing
    if sweepvar != 'cm_clinical': #if a case management level has not been assigned, we default to only present the smallest case manaagement value available in the data
        df = df[(df.cm_clinical == np.min(df.cm_clinical))]
    color_palette = sns.color_palette('Paired', len(df['emodom'].unique())) 
    firstPlot = True
    nx = len(df[sweepvar].unique())
    ny = len(seasonality)
    f = 1
    fig = plt.figure(figsize=(10*nx, 10*ny))
    for si, season in enumerate(seasonality):
        ax = fig.add_subplot(ny, nx, f)
        f += 1
        sdf = df[(df.seasonality == season)]
        for i, (p, pdf) in enumerate(sdf.groupby([sweepvar])):
            xmean, ymean = get_x_y(pdf, 'eir', eir_val, channel, use_std) #get values for x and y axes.
            merge_df = pd.merge(left = xmean, right = ymean, on = 'eir')
            merge_df.sort_values(by=eir_val, inplace=True)
            ax.plot(merge_df[eir_val], merge_df[channel], '-', linewidth=0.8, label=f"{p}", color=color_palette[i])
            ax.fill_between(merge_df[eir_val], merge_df[f'{channel}_min'], merge_df[f'{channel}_max'], alpha=0.1, color=color_palette[i])
        if firstPlot:
            lg = ax.legend(loc='upper left', bbox_to_anchor=(0.5, 1.2))
            firstPlot = False
        ax.set_xlim(0.1, 1000)
        ax.set_xscale('symlog')
        ax.set_xlabel(f'{eir_val.replace("EIR", " annual EIR")}', fontsize=14)
        if channel == 'prevalence2to10':
            ax.set_ylabel('$\it{Pf}$PR$_{2-10}$ (%)')
        else:
            ax.set_ylabel(f'{channel.replace("_"," ")}')
    fname = f'{eir_val}_{channel}_by_{sweepvar}_{agegrp}'
    fig.savefig(os.path.join(wdir, f'{fname}.png'), bbox_extra_artists=(lg,), bbox_inches='tight')
    plt.close()


# Plots input eir vs simulated eir, requires benchmark.csv
def input_to_simulated_eir(wdir, emodom, sweepvar='cm_clinical', use_std=False):
    """
    Generates line plots input compared to simulated EIR.
    Parameters:
        wdir (str): Working directory where the plot will be saved.
        emodom (str or list of str): Name of models for which result dataframes should be loaded.
        sweepvar (str, optional): Variable to group the data and create multiple lines on the plot. Default is 'cm_clinical'.
        use_std (bool, optional): Do you use two standard deviations for the fill (True) or percentiles (False). Default False.
    Returns:
        None (plots are saved to disk).
    """
    df, wdir = get_emodom_df(wdir, emodom)
    seasonality = list(df['seasonality'].unique())
    unique_groups = df['emodom'].unique()
    unique_groups = np.sort(unique_groups)
    num_colors = len(unique_groups)
    color_palette = sns.color_palette('Paired', num_colors)
    firstPlot = True

    if sweepvar != 'cm_clinical':
        df = df[(df.cm_clinical == np.min(df.cm_clinical))]

    nx = 1
    ny = len(seasonality)
    f = 1
    fig = plt.figure(figsize=(10*nx, 6*ny))
    for si, season in enumerate(seasonality):
        ax = fig.add_subplot(ny, nx, f)
        f += 1
        sdf = df[(df.seasonality == season)]
        for i, (p, pdf) in enumerate(sdf.groupby([sweepvar])):
            # plot mean, min and max of seeds and age groups
            xmean, ymean = get_x_y(pdf, 'eir', 'inputEIR', 'simulatedEIR', use_std)
            merge_df = pd.merge(left = xmean, right = ymean, on = 'eir')
            merge_df.sort_values(by='inputEIR', inplace=True)
            ax.plot(merge_df['inputEIR'], merge_df['simulatedEIR'], '-', linewidth=0.8, label=f"{p}", color=color_palette[i])
            ax.fill_between(merge_df['inputEIR'], merge_df['simulatedEIR_min'], merge_df['simulatedEIR_max'], alpha=0.1, color=color_palette[i])
        if firstPlot:
            lg = ax.legend(loc='upper left', bbox_to_anchor=(0.5, 1.2))  # , title='Model'
            firstPlot = False
        ax.set_ylim(0.1, 10000)
        ax.set_xlim(0.1, 10000)
        ax.set_yscale('symlog')
        ax.set_xscale('symlog')
    plt.xlabel('Input EIR')
    plt.ylabel('Simulated Annual EIR')
    #if ny == 2:
    #    fig.text(0.95, 0.25, seasonality[1], ha='center', va='center', rotation=-90, fontsize=14)
    fname = f'input_to_simulated_eir_by_{sweepvar}'
    fig.savefig(os.path.join(wdir, f'{fname}.png'), bbox_extra_artists=(lg,), bbox_inches='tight')
    plt.close()


# Plots trends over available months, requires Benchmark_mth.csv
def monthly_trends(wdir, emodom, channel, sweepvar='eir', use_std=False, agegrp='0-5'):
    """
    Generate line plots for monthly trends for channel (yaxis) by sweepvar for selected age groups.
    Note, assumed single occurence per month, i.e. aggregated across years (reads in benchmark_mth.csv)
    Parameters:
        wdir (str): Working directory where the plot will be saved.
        emodom (str or list of str): Name of models for which result dataframes should be loaded.
        channel (str): Variable representing the y-axis data to be plotted.
        sweepvar (str, optional): Variable to group the data and create multiple lines on the plot. Default is 'eir'.
        use_std (bool, optional): Do you use two standard deviations for the fill (True) or percentiles (False). Default False.
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
    color_palette = sns.color_palette('Paired', len(df['emodom'].unique()))
    nx = round(len(df[sweepvar].unique())/2)
    ny = 2
    f = 1
    firstPlot = True
    fig = plt.figure(figsize=(10*nx, 8*ny))
    new_index = [7,8,9,10,11,12,1,2,3,4,5,6] #To better showcase the montly trends, we present the months in this order
    for s in df[sweepvar].unique():
        sdf = df[(df[sweepvar] == s)]
        ax = fig.add_subplot(ny, nx, f)
        f += 1
        max_ylim = []
        for i, (m,mdf) in enumerate(sdf.groupby('emodom')):
            # plot mean, min and max of seeds
            ylim_up = np.max(mdf[channel])*1.1
            if channel == 'prevalence' or channel == 'prevalence_2to10':
                ylim_up = min(ylim_up, 1)
            max_ylim.append(ylim_up)
            xmean, ymean = get_x_y(mdf, 'month', channel, channel, use_std)
            for ii,ff in ymean.iterrows():
                ymean.loc[ii,'month'] = new_index[ii]
            xmean = xmean['month']
            merge_df = pd.merge(left = xmean, right = ymean, on = 'month')
            ax.plot(merge_df['month'], merge_df[channel], '-', linewidth=0.8, label=f"{m}", color=color_palette[i])
            ax.fill_between(merge_df['month'], merge_df[f'{channel}_min'], merge_df[f'{channel}_max'], alpha=0.1, color=color_palette[i])
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
    fig.savefig(os.path.join(wdir, f'{fname}.png'),bbox_extra_artists=(lg,), bbox_inches='tight')
    plt.close()


# Plots by sweeps and channels (currently pretty behind the other plotters, would need to be updated before use)
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
        use_std (bool, optional): Do you use two standard deviations for the fill (True) or percentiles (False). Default False.
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

    if len(unique_facets) == 1:
        axes = [axes]

    num_colors = len(unique_groups)
    color_palette = sns.color_palette('Paired', num_colors)

    # Iterate through each facet and plot the lines for each group
    for facet_value, ax in zip(unique_facets, axes.ravel()):
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
    fig.savefig(os.path.join(wdir, f'{fname}.png'))

    plt.legend(bbox_to_anchor=(0.5, 1.2), title=sweepvar, loc='upper left')
    plt.tight_layout()
    fig.savefig(os.path.join(wdir, f'{fname}_legend.png'))



def convert_to_date(x):
    import datetime
    return datetime.date(2005,1,1)+datetime.timedelta(days=x)

# Plots over time - requires PfPR_ClinicalIncidence_daily.csv
def daily_timeseries(wdir, emodom, channel_list, sweepvar='emodom', facet_var='ageGroup', use_std=False, agegrp='5-10'):
    """
    Parameters:
        wdir (str): Working directory where the plot will be saved.
        emodom (str or list of str): Name of models for which result dataframes should be loaded.
        channel (str): Variable representing the y-axis data to be plotted.
        sweepvar (str, optional): Variable to group the data and create multiple lines on the plot. Default is 'eir'.
        facet_var (str, optional): Variable used to create subplots based on its unique values. Default is 'ageGroup'. (The default should change)
        use_std (bool, optional): Do you use two standard deviations for the fill (True) or percentiles (False). Default False.
        agegrp (str, optional): Age group filter for the data. Default is '5-10'.
    Returns:
        None (plots are saved to disk).
    """    
    df_all, wdir = get_emodom_df(wdir, emodom, daily=True, timeseries=True)
    df_all = df_all[df_all['timestep'] >=1460] #remove the first 4 years of the 55 year monitoring period
    #df_all = df_all[df_all['timestep']<=14965] # remove the last 9 years of the 55 year monitoring period (don't really need to see these times, they don't show new info)
    df_all['day_date'] = df_all['timestep'].apply(convert_to_date)

    for channel in channel_list:
        print(f'#----- Plotting daily timeseries for {channel}-----#')
        if channel == 'prevalence_2to10':
            ylab = channel.replace('prevalence_2to10', '$\it{Pf}$PR$_{2-10}$ (%)')
        else:
            ylab = channel.replace('_', ' ')

        if facet_var != 'ageGroup' and agegrp is not None:
            df = df_all[(df_all.ageGroup == agegrp)]
        if agegrp is None:
            #df = df_all.groupby(['day_date', sweepvar, facet_var])[channel].agg(np.mean).reset_index()
            df = df_all.groupby(['day_date', sweepvar, facet_var])[channel].agg(np.mean).reset_index()

        if 'emodom' not in [sweepvar, facet_var] and len(df['emodom'].unique()) > 1:
            raise ValueError('emodom needs to be specified in plot if results were combined for more than 1 model')

        unique_facets = df[facet_var].unique()
        unique_facets = np.sort(unique_facets)
        color_palette = sns.color_palette('Paired', len(df[sweepvar].unique()))
        firstPlot = True
        nx = 2
        ny = 3
        f = 1
        fig = plt.figure(figsize=(10*nx, 10*ny))
        lower_prevalence = [0.1,0.1,0.25,0.25,0.5,0.5]
        upper_prevalence = [0.25,0.5,0.1,0.5,0.1,0.25]
        # Iterate through each facet and plot the lines for each group
        for ii, (facet, facet_df) in enumerate(df.groupby([facet_var])):
            ax = fig.add_subplot(ny,nx,f)
            f += 1
            max_ylim = []
            for i, model in enumerate(facet_df[sweepvar].unique()):
                model_df = facet_df[facet_df[sweepvar]==model]
                color = np.where(model == 'EMOD', 0, np.where(model=='MalSim', 1, np.where(model=='OpenMalaria', 2, 0)))
                xmean, ymean = get_x_y(model_df, 'day_date', channel, channel)
                if model == 'OpenMalaria' and channel =='simulatedEIR':
                    ymean[channel]= ymean[channel]/5
                    ymean[f'{channel}_min']= ymean[f'{channel}_min']/5
                    ymean[f'{channel}_max']=ymean[f'{channel}_max']/5
                xmean = xmean['day_date']
                merge_df = pd.merge(left = xmean, right = ymean, on = 'day_date')
                merge_df.sort_values(by='day_date', inplace=True)
                ax.plot(merge_df['day_date'], merge_df[channel], '-', linewidth=0.8, label=f"{model}", color=color_palette[color])
                x_min_note = merge_df.loc[merge_df['day_date']==min(merge_df['day_date'])][channel].iloc[0]
                x_max_note = merge_df.loc[merge_df['day_date']==max(merge_df['day_date'])][channel].iloc[0]
                year_factor = max(int((max(merge_df['day_date']).year - min(merge_df['day_date']).year)/8) , 1)
                ax.annotate(f"{round(x_min_note,2)}", xy=(min(merge_df['day_date']), x_min_note), xytext=(min(merge_df['day_date']), x_min_note-int(x_min_note/10)))
                ax.annotate(f"{round(x_max_note,2)}", xy=(max(merge_df['day_date']), x_max_note), xytext=(max(merge_df['day_date'])-pd.DateOffset(years=year_factor), x_max_note-int(x_min_note/15)))
                ylim_up = np.max(ymean[channel]) * 1.01
                if channel == 'prevalence' or channel == 'prevalence_2to10':
                    ylim_up = 1
                max_ylim.append(ylim_up)
            if channel == 'prevalence' or channel == 'prevalence_2to10':
                ax.axhline(lower_prevalence[ii], linestyle = '--')
                ax.axhline(upper_prevalence[ii], linestyle = '--')
            if firstPlot:
                lg = ax.legend(loc='upper left', bbox_to_anchor=(0.5, 1.4))
                #lg = ax.legend(loc='upper left', bbox_to_anchor=(1,0.7))
                firstPlot = False
            ax.set_ylabel(ylab)
            ax.set_ylim(0, max(max_ylim))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=8))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
            ax.set_xlabel('Year')
            ax.set_title('$\it{Pf}$PR$_{2-10}$'+f': {facet}')
        fname = f'timeseries_daily_{channel}_by_{sweepvar}_age{agegrp}'
        fig.savefig(os.path.join(wdir, f'{fname}.png'), bbox_extra_artists=(lg,), bbox_inches='tight')
        plt.close()

# Plots over time - requires PfPR_ClinicalIncidence_daily.csv
def daily_timeseries_by_seed(wdir, emodom, channel_list, sweepvar='emodom', facet_var='ageGroup', use_std=False, agegrp='5-10'):
    """
    Parameters:
        wdir (str): Working directory where the plot will be saved.
        emodom (str or list of str): Name of models for which result dataframes should be loaded.
        channel (str): Variable representing the y-axis data to be plotted.
        sweepvar (str, optional): Variable to group the data and create multiple lines on the plot. Default is 'eir'.
        facet_var (str, optional): Variable used to create subplots based on its unique values. Default is 'ageGroup'. (The default should change)
        use_std (bool, optional): Do you use two standard deviations for the fill (True) or percentiles (False). Default False.
        agegrp (str, optional): Age group filter for the data. Default is '5-10'.
    Returns:
        None (plots are saved to disk).
    """    
    df_all, wdir = get_emodom_df(wdir, emodom, daily=True, timeseries=True)
    df_all = df_all[df_all['timestep'] >= 1460] #remove the first 4 years of the 55 year monitoring period
    df_all['day_date'] = df_all['timestep'].apply(convert_to_date)

    for channel in channel_list:
        print(f'#----- Plotting daily timeseries for {channel}-----#')
        if channel == 'prevalence_2to10':
            ylab = channel.replace('prevalence_2to10', '$\it{Pf}$PR$_{2-10}$ (%)')
        else:
            ylab = channel.replace('_', ' ')

        if facet_var != 'ageGroup' and agegrp is not None:
            df = df_all[(df_all.ageGroup == agegrp)]
        if agegrp is None:
            #df = df_all.groupby(['day_date', sweepvar, facet_var])[channel].agg(np.mean).reset_index()
            df = df_all.groupby(['day_date', sweepvar, facet_var,'seed'])[channel].agg(np.mean).reset_index()

        if 'emodom' not in [sweepvar, facet_var] and len(df['emodom'].unique()) > 1:
            raise ValueError('emodom needs to be specified in plot if results were combined for more than 1 model')

        unique_facets = df[facet_var].unique()
        unique_facets = np.sort(unique_facets)
        color_palette = sns.color_palette('Paired', len(df['seed'].unique()))
        nx = 2
        ny = 3
        f = 1
        lower_prevalence = [0.1,0.1,0.25,0.25,0.5,0.5]
        upper_prevalence = [0.25,0.5,0.1,0.5,0.1,0.25]
        # Iterate through each facet and plot the lines for each group
        for m, model in enumerate(df[sweepvar].unique()):
            model_df = df[df[sweepvar]==model]
            fig = plt.figure(figsize=(10*nx, 10*ny))
            f=1
            for i, (facet, facet_df) in enumerate(model_df.groupby([facet_var])):
                ax = fig.add_subplot(ny,nx,f)
                f = f+1
                for si, (seeds, sdf) in enumerate(facet_df.groupby(['seed'])):
                    xmean, ymean = get_x_y(sdf, 'day_date', channel, channel)
                    if model == 'OpenMalaria' and channel =='simulatedEIR':
                        ymean[channel]= ymean[channel]/5
                        ymean[f'{channel}_min']= ymean[f'{channel}_min']/5
                        ymean[f'{channel}_max']=ymean[f'{channel}_max']/5
                    xmean = xmean['day_date']
                    merge_df = pd.merge(left = xmean, right = ymean, on = 'day_date')
                    merge_df.sort_values(by='day_date', inplace=True)
                    ax.plot(merge_df['day_date'], merge_df[channel], '-', linewidth=0.8, label=f"{si}", color=color_palette[si])
                    x_min_note = merge_df.loc[merge_df['day_date']==min(merge_df['day_date'])][channel].iloc[0]
                    x_max_note = merge_df.loc[merge_df['day_date']==max(merge_df['day_date'])][channel].iloc[0]
                    year_factor = max(int((max(merge_df['day_date']).year - min(merge_df['day_date']).year)/8) , 1)
                    ax.annotate(f"{round(x_min_note,2)}", xy=(min(merge_df['day_date']), x_min_note), xytext=(min(merge_df['day_date']), x_min_note-int(x_min_note/10)))
                    ax.annotate(f"{round(x_max_note,2)}", xy=(max(merge_df['day_date']), x_max_note), xytext=(max(merge_df['day_date'])-pd.DateOffset(years=year_factor), x_max_note-int(x_min_note/15)))
                if channel == 'prevalence' or channel == 'prevalence_2to10':
                        ax.axhline(lower_prevalence[i], linestyle = '--')
                        ax.axhline(upper_prevalence[i], linestyle = '--')
                ax.set_ylabel(ylab)
                ax.set_ylim(0,1)
                ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=8))
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
                ax.set_xlabel('Year')
                ax.set_title(f'{model}: {facet}')
            fname = f'timeseries_daily_{channel}_by_{model}_age{agegrp}_by_seed'
            fig.savefig(os.path.join(wdir, f'{fname}.png'), bbox_inches='tight')
            #fig.savefig(os.path.join(wdir, f'{fname}.pdf'), bbox_inches='tight')
            plt.close()

# Plots over time - requires PfPR_ClinicalIncidence_daily.csv
def daily_vectors(wdir, emodom, channel, sweepvar='emodom', facet_var='ageGroup', use_std=False, agegrp='5-10'):
    """
    Parameters:
        wdir (str): Working directory where the plot will be saved.
        emodom (str or list of str): Name of models for which result dataframes should be loaded.
        channel (str): Variable representing the y-axis data to be plotted.
        sweepvar (str, optional): Variable to group the data and create multiple lines on the plot. Default is 'eir'.
        facet_var (str, optional): Variable used to create subplots based on its unique values. Default is 'ageGroup'. (The default should change)
        use_std (bool, optional): Do you use two standard deviations for the fill (True) or percentiles (False). Default False.
        agegrp (str, optional): Age group filter for the data. Default is '5-10'.
    Returns:
        None (plots are saved to disk).
    """    
    df_all, wdir = get_emodom_df(wdir, emodom, daily=True, timeseries=True)
    df_all = df_all[df_all['timestep'] >= 1460]
    df_all['day_date'] = df_all['timestep'].apply(convert_to_date)


    ylab = channel.replace('_', ' ')

    if facet_var != 'ageGroup' and agegrp is not None:
        df = df_all[(df_all.ageGroup == agegrp)]
    if agegrp is None:
        df = df_all.groupby(['day_date', sweepvar, facet_var])[channel].agg(np.mean).reset_index()

    if 'emodom' not in [sweepvar, facet_var] and len(df['emodom'].unique()) > 1:
        raise ValueError('emodom needs to be specified in plot if results were combined for more than 1 model')

    unique_facets = df[facet_var].unique()
    unique_facets = np.sort(unique_facets)
    color_palette = sns.color_palette('Paired', len(df[sweepvar].unique()))
    firstPlot = True
    nx = 2
    ny = 3
    f = 1

    # Iterate through each facet and plot the lines for each group
    for zz,ii in enumerate(df[sweepvar].unique()):
        fig = plt.figure(figsize=(10*nx, 10*ny))
        f = 1
        sdf = df[df[sweepvar] == ii]
        for i, (fi, fdf) in enumerate(sdf.groupby([facet_var])):
            ax = fig.add_subplot(ny,nx,f)
            f += 1
            xmean, ymean = get_x_y(fdf, 'day_date', channel, channel)
            xmean = xmean['day_date']
            merge_df = pd.merge(left = xmean, right = ymean, on = 'day_date')
            merge_df.sort_values(by='day_date', inplace=True)
            ax.plot(merge_df['day_date'], merge_df[channel], '-', linewidth=0.8, label=f"{fi}", color=color_palette[zz])
            ax.fill_between(merge_df['day_date'], merge_df[f'{channel}_min'], merge_df[f'{channel}_max'], alpha=0.2, color=color_palette[zz])
            ylim_up = np.max(ymean[channel]) * 1.01
            x_min_note = merge_df.loc[merge_df['day_date']==min(merge_df['day_date'])][channel].iloc[0]
            x_max_note = merge_df.loc[merge_df['day_date']==max(merge_df['day_date'])][channel].iloc[0]
            year_factor = max(int((max(merge_df['day_date']).year - min(merge_df['day_date']).year)/8) , 1)
            ax.annotate(f"{round(x_min_note,2)}", xy=(min(merge_df['day_date']), x_min_note), xytext=(min(merge_df['day_date']), x_min_note-int(x_min_note/10)))
            ax.annotate(f"{round(x_max_note,2)}", xy=(max(merge_df['day_date']), x_max_note), xytext=(max(merge_df['day_date'])-pd.DateOffset(years=year_factor), x_max_note-int(x_min_note/15)))
            if firstPlot:
                lg = ax.legend(loc='upper left', bbox_to_anchor=(0.5, 1.4))
                firstPlot = False
            ax.set_ylabel(ylab)
            ax.set_ylim(0, ylim_up)
            ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=8))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
            ax.set_xlabel('Year')
            ax.set_title('$\it{Pf}$PR$_{2-10}$'+f': {fi}')
        fname = f'timeseries_daily_{channel}_by_{ii}_age{agegrp}'
        fig.savefig(os.path.join(wdir, f'{fname}.png'), bbox_extra_artists=(lg,), bbox_inches='tight')
        plt.close()


# Plots over time - requires PfPR_ClinicalIncidence_mth.csv
def monthly_timeseries(wdir, emodom, channel, sweepvar='emodom', facet_var='ageGroup', use_std=False, agegrp='5-10'):
    """
    Parameters:
        wdir (str): Working directory where the plot will be saved.
        emodom (str or list of str): Name of models for which result dataframes should be loaded.
        channel (str): Variable representing the y-axis data to be plotted.
        sweepvar (str, optional): Variable to group the data and create multiple lines on the plot. Default is 'eir'.
        facet_var (str, optional): Variable used to create subplots based on its unique values. Default is 'ageGroup'. (The default should change)
        use_std (bool, optional): Do you use two standard deviations for the fill (True) or percentiles (False). Default False.
        agegrp (str, optional): Age group filter for the data. Default is '5-10'.
    Returns:
        None (plots are saved to disk).
    """   
    df, wdir = get_emodom_df(wdir, emodom, mth=True, timeseries=True)

    if channel == 'prevalence_2to10':
        ylab = channel.replace('prevalence_2to10', '$\it{Pf}$PR$_{2-10}$ (%)')
    else:
        ylab = channel.replace('_', ' ')

    if facet_var != 'ageGroup' and agegrp is not None:
        df = df[(df.ageGroup == agegrp)]
    df['date'] = pd.to_datetime(df['date'])
    if agegrp is None:
        df = df.groupby(['date','seed', 'seasonality','cm_clinical', sweepvar, facet_var])[channel].agg(np.mean).reset_index()

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
    color_palette = sns.color_palette('Paired', len(df[sweepvar].unique()))
    firstPlot = True
    nx = round(len(df[facet_var].unique())/2)
    ny = 2
    f = 1
    fig = plt.figure(figsize=(10*nx, 10*ny))
    # Iterate through each facet and plot the lines for each group
    for fi in unique_facets:
        fdf = df[df[facet_var] == fi]
        ax = fig.add_subplot(ny,nx,f)
        f += 1
        max_ylim = []
        for i, (s, sdf) in enumerate(fdf.groupby([sweepvar])):
            ylim_up = np.max(sdf[channel]) * 1.1
            if channel == 'prevalence' or channel == 'prevalence_2to10':
                ylim_up = min(ylim_up, 1)
            max_ylim.append(ylim_up)
            xmean, ymean = get_x_y(sdf, 'date', channel, channel, use_std)
            xmean = xmean['date']
            merge_df = pd.merge(left = xmean, right = ymean, on = 'date')
            merge_df.sort_values(by='date', inplace=True)
            ax.plot(merge_df['date'], merge_df[channel], '-', linewidth=0.8, label=f"{s}", color=color_palette[i])
            ax.fill_between(merge_df['date'], merge_df[f'{channel}_min'], merge_df[f'{channel}_max'], alpha=0.1, color=color_palette[i])
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
def annual_timeseries(wdir, emodom, channel, sweepvar='emodom', facet_var='ageGroup', use_std=False, agegrp='5-10'):
    """
    Parameters:
        wdir (str): Working directory where the plot will be saved.
        emodom (str or list of str): Name of models for which result dataframes should be loaded.
        channel (str): Variable representing the y-axis data to be plotted.
        sweepvar (str, optional): Variable to group the data and create multiple lines on the plot. Default is 'eir'.
        facet_var (str, optional): Variable used to create subplots based on its unique values. Default is 'ageGroup'. (The default should change)
        use_std (bool, optional): Do you use two standard deviations for the fill (True) or percentiles (False). Default False.
        agegrp (str, optional): Age group filter for the data. Default is '5-10'.
    Returns:
        None (plots are saved to disk).
    """   
    df, wdir = get_emodom_df(wdir, emodom, mth=False, timeseries=True)

    if channel == 'prevalence_2to10':
        ylab = channel.replace('prevalence_2to10', '$\it{Pf}$PR$_{2-10}$ (%)')
    else:
        ylab = channel.replace('_', ' ')

    if facet_var != 'ageGroup' and agegrp is not None:
        df = df[(df.ageGroup == agegrp)]
    if agegrp is None:
        df = df.groupby(['year','seed', 'seasonality','cm_clinical', sweepvar, facet_var])[channel].agg(np.mean).reset_index()
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
    
    color_palette = sns.color_palette('Paired', len(df[sweepvar].unique()))
    firstPlot = True
    nx = round(len(unique_facets)/2)
    ny = 2
    f = 1
    fig = plt.figure(figsize=(10*nx,11*ny))
    for fi in unique_facets:
        fdf = df[df[facet_var] == fi]
        ax = fig.add_subplot(ny,nx,f)
        f += 1
        max_ylim = []
        for i, (s, sdf) in enumerate(fdf.groupby([sweepvar])):
            ylim_up = np.max(sdf[channel]) * 1.1
            if channel == 'prevalence' or channel == 'prevalence_2to10':
                ylim_up = min(ylim_up,1)
            max_ylim.append(ylim_up)
            xmean, ymean = get_x_y(sdf, 'year', channel, channel, use_std)
            xmean = xmean['year']
            merge_df = pd.merge(left = xmean, right = ymean, on = 'year')
            merge_df.sort_values(by='year', inplace=True)
            ax.plot(merge_df['year'], merge_df[channel], '-', linewidth=0.8, label=f"{s}", color=color_palette[i])
            ax.fill_between(merge_df['year'], merge_df[f'{channel}_min'], merge_df[f'{channel}_max'], alpha=0.1, color=color_palette[i])
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


# Plots over age - requires PfPR_ClinicalIncidence_yr.csv
def age_curves(wdir, emodom, channel, sweepvar='emodom', facet_var='seasonality', use_std=False):
    """
    Parameters:
        wdir (str): Working directory where the plot will be saved.
        emodom (str or list of str): Name of models for which result dataframes should be loaded.
        channel (str): Variable representing the y-axis data to be plotted.
        sweepvar (str, optional): Variable to group the data and create multiple lines on the plot. Default is 'emodom'.
        facet_var (str, optional): Variable used to create subplots based on its unique values. Default is 'seasonality'. 
        use_std (bool, optional): Do you use two standard deviations for the fill (True) or percentiles (False). Default False.
    Returns:
        None (plots are saved to disk).
    """   
    df, wdir = get_emodom_df(wdir, emodom, mth=False, timeseries=True)
    
    if channel == 'prevalence_2to10':
        ylab = channel.replace('prevalence_2to10', '$\it{Pf}$PR$_{2-10}$ (%)')
    else:
        ylab = channel.replace('_', ' ')
    
    if facet_var == 'ageGroup':
        facet_var = 'eir'
    if 'cm_clinical' not in [sweepvar, facet_var]:
        selected_cm = np.min(df.cm_clinical)
        df = df[(df.cm_clinical == selected_cm)]

    if 'seasonality' not in [sweepvar, facet_var]:
        selected_season = df['seasonality'].unique()[0]
        df = df[(df.seasonality == selected_season)]

    if 'eir' not in [sweepvar, facet_var]:
        selected_eir = np.max(df.eir)
        df = df[(df.eir == selected_eir)]

    if 'emodom' not in [sweepvar, facet_var] and len(df['emodom'].unique()) > 1:
        raise ValueError('emodom needs to be specified in plot if results were combined for more than 1 model')
    df = df.groupby(['ageGroup', 'seed', sweepvar, facet_var])[channel].agg(np.mean).reset_index()

    firstPlot = True
    unique_facets = df[facet_var].unique()
    unique_facets = sorted(unique_facets)
    color_palette = sns.color_palette('Paired', len(df[sweepvar].unique()))

    nx = round(len(unique_facets)/2)
    ny = 2
    f = 1
    fig = plt.figure(figsize=(10*nx,10*ny))
    for fi in unique_facets:
        fdf = df[df[facet_var] == fi]
        fdf = fdf[fdf[channel].notnull()]
        ax = fig.add_subplot(ny,nx,f)
        f += 1
        max_ylim = []
        for i, (s, sdf) in enumerate(fdf.groupby([sweepvar])):  
            ylim_up = np.max(sdf[channel])*1.1
            if channel == 'prevalence' or channel == 'prevalence_2to10':
                ylim_up = min(ylim_up,1) 
            max_ylim.append(ylim_up)
            xmean, ymean = get_x_y(sdf, 'ageGroup', channel, channel, use_std)
            xmean = xmean['ageGroup']
            merge_df = pd.merge(left = xmean, right = ymean, on = 'ageGroup')
            merge_df['ageGroup'] = pd.Categorical(merge_df['ageGroup'], ['0-0.5','0.5-1','1-2','2-5','5-10','10-15','15-20','20-100'])
            merge_df.sort_values('ageGroup', inplace=True)
            ax.plot(merge_df['ageGroup'], merge_df[channel], '-', linewidth=0.8, label=f"{s}", color=color_palette[i])
            ax.fill_between(merge_df['ageGroup'], merge_df[f'{channel}_min'], merge_df[f'{channel}_max'], alpha=0.1, color=color_palette[i])
        if firstPlot:
            lg = ax.legend(loc='upper left', bbox_to_anchor=(0.5, 1.2))
            firstPlot = False
        ax.set_ylim(0, max(max_ylim))
        ax.tick_params(axis='x', labelrotation = 45)
        ax.set_xlabel('Age (years)')
        ax.set_ylabel(ylab)
        ax.set_title(f"{facet_var} = {fi}")
    fname = f'agecurves_{channel}_by_{sweepvar}'
    fig.savefig(os.path.join(wdir, f'{fname}.png'), bbox_extra_artists=(lg,), bbox_inches='tight')
    plt.close()


# Calculates ANOVA scores for each output variable, requires Benchmark.csv
def anovas(wdir, emodom):
    """
    Calculates ANOVA scores for each output variable, seperated by age group and all ages.
    Parameters:
        wdir (str): Working directory where the plot will be saved.
        emodom (str or list of str): Name of models for which result dataframes should be loaded.
    Returns:
        None (ANOVA values are saved to disk).
    """ 
    from scipy.stats import f_oneway
    df, wdir = get_emodom_df(wdir, emodom, mth=False, timeseries=False)
    comparisons = ['prevalence_2to10', 'prevalence', 'clinical_incidence', 'severe_incidence', 'simulatedEIR']
    emod = df[df['emodom'] == 'EMOD']
    malsim = df[df['emodom'] == 'MalSim']
    openmalaria = df[df['emodom'] == 'OpenMalaria']

    anova_df = pd.DataFrame(columns=['Age Group', 'Objective', 'F_value', 'p_value', 'null_hyp'])

    # As a whole
    for com in comparisons:
        performance_emod = emod[com]
        performance_malsim = malsim[com]
        performance_openmalaria = openmalaria[com]
        f_value, p_value = f_oneway(performance_emod, performance_malsim, performance_openmalaria)
        if p_value <= 0.05:
            null_hyp = True
        else:
            null_hyp = False
        new_row = {'Age Group': 'Across All Ages', 'Objective': com, 'F_value': f_value, 'p_value': p_value,
                   'null_hyp': null_hyp}
        anova_df = pd.concat([anova_df, pd.DataFrame([new_row])], ignore_index=True)

    # By Age Group
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
            new_row = {'Age Group': age, 'Objective': com, 'F_value': f_value, 'p_value': p_value, 'null_hyp': null_hyp}
            anova_df = pd.concat([anova_df, pd.DataFrame([new_row])], ignore_index=True)

    anova_df.to_csv(os.path.join(wdir, 'anovas.csv'), index=False)


# Calculates RMSE values for each output variable
def rmse(wdir, emodom):
    """
    Calculates RMSE scores for each output variable (comparing against each model individually), seperated by age group and all ages.
    Parameters:
        wdir (str): Working directory where the plot will be saved.
        emodom (str or list of str): Name of models for which result dataframes should be loaded.
    Returns:
        None (RMSE scores are saved to disk).
    """ 
    from sklearn.metrics import mean_squared_error
    from math import sqrt
    df, wdir = get_emodom_df(wdir, emodom, mth=False, timeseries=False)
    rmse_vars = ['prevalence_2to10', 'prevalence', 'clinical_incidence', 'severe_incidence', 'simulatedEIR']

    rmse_df = pd.DataFrame(
        columns=['Age Group', 'Variable', 'EMOD_TO_OPENMALARIA', 'OPENMALARIA_TO_MALSIM', 'EMOD_TO_MALSIM'])

    for rmse_var in rmse_vars:
        group_data = df.groupby(['emodom'])[rmse_var].agg(['mean']).reset_index()
        emod_data = group_data[group_data['emodom'] == 'EMOD']
        malsim_data = group_data[group_data['emodom'] == 'MalSim']
        om_data = group_data[group_data['emodom'] == 'OpenMalaria']
        # RMSE Between EMOD and OM
        rmse_eo = sqrt(mean_squared_error(emod_data['mean'], om_data['mean']))
        # RMSE Between OM AND MALSIM
        rmse_om = sqrt(mean_squared_error(malsim_data['mean'], om_data['mean']))
        # RMSE Between EMOD and Malsim
        rmse_em = sqrt(mean_squared_error(emod_data['mean'], malsim_data['mean']))
        # RMSE Concat
        new_row = {'Age Group': 'Across All Ages', 'Variable': rmse_var, 'EMOD_TO_OPENMALARIA': rmse_eo,
                   'OPENMALARIA_TO_MALSIM': rmse_om, 'EMOD_TO_MALSIM': rmse_em}
        rmse_df = pd.concat([rmse_df, pd.DataFrame([new_row])], ignore_index=True)

    for age in df['ageGroup'].unique():
        adf = df[df['ageGroup'] == age]
        for rmse_var in rmse_vars:
            group_data = adf.groupby(['emodom'])[rmse_var].agg(['mean']).reset_index()
            emod_data = group_data[group_data['emodom'] == 'EMOD']
            malsim_data = group_data[group_data['emodom'] == 'MalSim']
            om_data = group_data[group_data['emodom'] == 'OpenMalaria']
            # RMSE Between EMOD and OM
            rmse_eo = sqrt(mean_squared_error(emod_data['mean'], om_data['mean']))
            # RMSE Between OM AND MALSIM
            rmse_om = sqrt(mean_squared_error(malsim_data['mean'], om_data['mean']))
            # RMSE Between EMOD and Malsim
            rmse_em = sqrt(mean_squared_error(emod_data['mean'], malsim_data['mean']))
            # RMSE DF
            new_row = {'Age Group': age, 'Variable': rmse_var, 'EMOD_TO_OPENMALARIA': rmse_eo,
                       'OPENMALARIA_TO_MALSIM': rmse_om, 'EMOD_TO_MALSIM': rmse_em}
            rmse_df = pd.concat([rmse_df, pd.DataFrame([new_row])], ignore_index=True)
    rmse_df.to_csv(os.path.join(wdir, 'rmse.csv'), index=False)


if __name__ == "__main__":
    args = parse_args()
    out_dir = args.directory
    emodom = args.emodom
    #out_dir = 
    #emodom = ['EMOD', 'OpenMalaria', 'MalSim']
    if isinstance(emodom, str):
        emodom = [emodom]
    file = open(os.path.join(out_dir, "exp.obj"), "rb")
    exp = pickle.load(file)

    eir_relationship_plots = True # uses 'Benchmark.csv' output files
    timeseries_plots = True # requires disaggregated result csvs (PfPR_ClinicalIncidence_<mth/yr/daily>.csv
    quantitative = False

    if quantitative:
       # Currently RMSE and ANOVAS are hard coded to require all three models
        print('#----- Calculating RMSE Values and ANOVAs -----#')
        rmse(out_dir, emodom)
        anovas(out_dir, emodom)

    if eir_relationship_plots and len(exp.eir) >= 3 and 'cc_step' not in exp.intervention_list:
        eir_relationship_plots = True
    else:
        eir_relationship_plots = False

    if eir_relationship_plots:
        sweepvar = 'emodom'
        print('#----- Plotting input to simulated EIR -----#')
        input_to_simulated_eir(out_dir, emodom, sweepvar=sweepvar)

        channel_list = ['prevalence_2to10', 'prevalence', 'clinical_incidence', 'severe_incidence']
        for channel in channel_list:
            print(f'#----- Plotting simulated EIR to {channel} -----#')
            eir_to_outcome(out_dir, emodom, sweepvar=sweepvar, eir_val='simulatedEIR', channel = channel, use_std=False, agegrp = '0-100') #Jaline prefers 0-100 visuals

        channel_list = ['clinical_incidence', 'severe_incidence', 'prevalence', 'simulatedEIR']
        for channel in channel_list:
            print(f'#----- Plotting prevalence_2_to_10 to {channel} -----#')
            prevalence2to10_to_incidence(out_dir, emodom, channel=channel)
            #prevalence2to10_to_incidence_by_age_and_model(out_dir,emodom,channel=channel) #This is new plotter, we don't have to make it everytime, but its available.
        if exp.om_survey_step == '30d' and exp.emod_step != 'burnin':
            channel_list = ['clinical_incidence', 'severe_incidence', 'prevalence', 'simulatedEIR', 'prevalence_2to10']
            sweepvar = 'eir'
            for channel in channel_list:
                try:
                    print(f'#----- Plotting the monthly trends for {channel} -----#')
                    monthly_trends(out_dir, emodom, channel=channel, sweepvar=sweepvar, use_std = False, agegrp = '0-100') #0-100
                except:
                    print(f'{channel} not found in dataframe')    

    # Additional standardized plots - timeseries
    if timeseries_plots:
        channel_list = ['clinical_incidence', 'severe_incidence', 'prevalence', 'simulatedEIR', 'prevalence_2to10'] 
        sweepvar = 'emodom'
        facet_var = 'ageGroup'
        if len(exp.eir) > 1 & len(exp.eir) <= 3:
            facet_var = 'eir'
        if facet_var == 'ageGroup' and len(exp.cm_clinical) > 1:
            facet_var = 'cm_clinical'
        if facet_var == 'ageGroup' and len(exp.seasonality) > 1:
            facet_var = 'seasonality'

        if 'cc_step' in exp.intervention_list and exp.emod_step != 'burnin':
            daily_channel_list = ['prevalence_2to10','prevalence','simulatedEIR','clinical_incidence','severe_incidence']
            facet_daily = 'carrying_capacity_step'            
            daily_timeseries(out_dir, emodom, channel_list = daily_channel_list, sweepvar = sweepvar, facet_var = facet_daily, agegrp = None) #if you set agegrp to None, it will combine all ages
            #daily_timeseries_by_seed(out_dir, emodom, channel_list = daily_channel_list, sweepvar = sweepvar, facet_var = facet_daily, agegrp = None)
            daily_vectors(out_dir, emodom, channel = 'n_total_mos_pop', sweepvar = sweepvar, facet_var = facet_daily, agegrp = None)
        else:
            for channel in channel_list:
                if exp.om_survey_step == '30d' and exp.emod_step != 'burnin':
                    print(f'#----- Plotting monthly timeseries for {channel}-----#')
                    monthly_timeseries(out_dir, emodom, channel=channel, sweepvar=sweepvar, facet_var=facet_var, agegrp=None) #if you set agegrp to None, it will combine all ages
                print(f'#----- Plotting annual timeseries for {channel}-----#')
                annual_timeseries(out_dir, emodom, channel=channel, sweepvar=sweepvar, facet_var=facet_var, agegrp=None) #if you set agegrp to None, it will combine all ages
                
                if not channel =='simulatedEIR':
                    print(f'#----- Plotting Age Curves for {channel}-----#')
                    age_curves(out_dir, emodom, channel=channel, sweepvar=sweepvar, facet_var=facet_var)
     
    """        
    # Additional standardized plots - line colors by sweep variable
    sweep_plots = False  # requires customization depending on variables sweep over to plot
    if sweep_plots:
        print('#----- Running sweep_plots -----#')
        channel_list = ['clinical_incidence', 'severe_incidence', 'prevalence', 'prevalence_2to10']  # 'simulatedEIR'
        x_var = 'cm_clinical'
        sweepvar = 'emodom'
        facet_var = 'eir'
        for channel in channel_list:
            sweep_by_channel_plot(out_dir, emodom, x_var=x_var, channel=channel, sweepvar=sweepvar, facet_var=facet_var)
    """
