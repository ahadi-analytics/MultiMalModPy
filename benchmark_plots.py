import argparse
import pickle
import os
import numpy as np
import pandas as pd
import matplotlib as mpl
import seaborn as sns

# mpl.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker

mpl.rcParams['pdf.fonttype'] = 42


# mpl.rc('font', **{'family': 'sans-serif', 'sans-serif': ['Helvetica']})
# mpl.rc('text', usetex=True)


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
    if 'MalSim' in emodom:
        ms_df = pd.read_csv((os.path.join(wdir, f'MalSim/{fname}')))
        ms_df['emodom'] = 'MalSim' 
        ms_df['simulatedEIR'] = ms_df['eir'] 
        ms_df['inputEIR'] = ms_df['eir']   
                                   
    if 'EMOD' in emodom and 'OpenMalaria' in emodom and 'MalSim' in emodom:
        df = em_df.append(om_df)
        df = df.append(ms_df)
        df.to_csv('out.csv', index=False)
    elif 'OpenMalaria' in emodom and 'EMOD' in emodom and not 'MalSim' in emodom:
        df = em_df.append(om_df)
    elif 'OpenMalaria' in emodom and 'MalSim' in emodom and not 'EMOD' in emodom:
        df = ms_df.append(om_df)
    elif 'EMOD' in emodom and 'MalSim' in emodom and not 'OpenMalaria' in emodom:
        df = om_df.append(ms_df)
    elif 'OpenMalaria' and not 'EMOD' in emodom and not 'MalSim' in emodom:
        wdir = os.path.join(wdir, 'om')
        df = om_df
    elif 'EMOD' and not 'OpenMalaria' in emodom and not 'MalSim' in emodom:
        wdir = os.path.join(wdir, 'em')
        df = em_df
    elif 'MalSim' and not 'OpenMalaria' in emodom and not 'EMOD' in emodom:
        wdir = os.path.join(wdir, 'MalSim')
        df = ms_df
    else:
        raise ValueError(f"Please specify emodom as some combination of EMOD, OpenMalaria, and MalSim (list), {emodom} not valid")

    if 'ageGroup' in df.columns:
        age_grps = list(df['ageGroup'].unique())
        df['ageGroup'] = df['ageGroup'].astype('category')
        df['ageGroup'] = df['ageGroup'].cat.reorder_categories(age_grps)

    return df, wdir


def prevalence2to10_to_incidence(wdir, emodom, channel='clinical_incidence', y_lim=6):
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

    nx = len(emodom)
    ny = len(seasonality)
    f = 1
    firstPlot = True
    fig = plt.figure(figsize=(7, 6))

    # for each age group, plot x = prevalence 2_to_10, y = incidences

    for si, season in enumerate(seasonality):
        for mi, model in enumerate(emodom):
            ax = fig.add_subplot(ny, nx, f);
            f += 1;
            sdf = df[(df.seasonality == season) & (df.emodom == model)]
            for p, pdf in sdf.groupby(['ageGroup']):
                ages = pdf['ageGroup'].unique()
                # plot mean, min and max of seeds
                xvalues = pdf.groupby('eir')['prevalence_2to10'].agg(np.mean)
                ymean = pdf.groupby('eir')[channel].agg(np.mean)
                ymin = pdf.groupby('eir')[channel].agg(np.min)
                ymax = pdf.groupby('eir')[channel].agg(np.max)
                ax.plot(xvalues, ymean, label=ages[0] if firstPlot else "")
                ax.fill_between(xvalues, ymin, ymax, alpha=0.3)

            ax.set_ylim(0, y_lim)
            ax.set_xlim(0, 1)
            ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1])
            if firstPlot: lg = ax.legend(loc="upper left",
                                         title="age group")  # , title_fontproperties={"weight": "bold"}
            firstPlot = False

    fig.text(0.5, 0.02, '$\it{Pf}$PR$_{2-10}$ (%)', ha='center', va='center', fontsize=14)
    fig.text(0.02, 0.5, title, ha='center', va='center', rotation='vertical', fontsize=14)
    fig.text(0.98, 0.75, seasonality[0], ha='center', va='center', rotation=-90, fontsize=14)
    fig.text(0.25, 0.98, df.emodom.unique()[0], ha='center', va='center', fontsize=14)
    if ny == 2:
        fig.text(0.98, 0.25, seasonality[1], ha='center', va='center', rotation=-90, fontsize=14)
    if nx == 2:
        fig.text(0.75, 0.98, df.emodom.unique()[1], ha='center', va='center', fontsize=14)
    plt.tight_layout(rect=[0.025, 0.025, 0.985, 0.985])

    fname = f'pfpr2to10_to_{channel}'
    fig.savefig(os.path.join(wdir, f'{fname}.png'), bbox_extra_artists=(lg,))
    # fig.savefig(os.path.join(wdir, f'{fname}.pdf'), bbox_extra_artists=(lg,))


def eir_to_prevalence2to10(wdir, emodom, sweepvar='cm_clinical', eir_val='simulatedEIR'):
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

    nx = 1
    ny = len(seasonality)
    f = 1
    firstPlot = True
    fig = plt.figure(figsize=(6, 6))
    for si, season in enumerate(seasonality):
        ax = fig.add_subplot(ny, nx, f);
        f += 1;
        sdf = df[(df.seasonality == season)]
        for p, pdf in sdf.groupby([sweepvar]):
            # plot mean, min and max of seeds and age groups
            xmean = pdf.groupby('eir')[eir_val].agg(np.mean)
            ymean = pdf.groupby('eir')['prevalence_2to10'].agg(np.mean)
            ymin = pdf.groupby('eir')['prevalence_2to10'].agg(np.min)
            ymax = pdf.groupby('eir')['prevalence_2to10'].agg(np.max)
            ax.plot(xmean, ymean, '-', linewidth=0.8, label=f"{p}")
            ax.fill_between(xmean, ymin, ymax, alpha=0.3)

        ax.set_ylim(0, 1)
        ax.set_xlim(0.1, 100000)
        ax.set_xscale('symlog')
        ax.set_xlabel(f'{eir_val.replace("EIR", " annual EIR")}', fontsize=14)
        if firstPlot: lg = ax.legend(loc="upper left")  # title=sweepvar, title_fontproperties={"weight": "bold"}
        firstPlot = False

    fig.text(0.02, 0.5, '$\it{Pf}$PR$_{2-10}$', ha='center', va='center', rotation='vertical', fontsize=14)
    fig.text(0.95, 0.75, seasonality[0], ha='center', va='center', rotation=-90, fontsize=14)
    if ny == 2:
        fig.text(0.95, 0.25, seasonality[1], ha='center', va='center', rotation=-90, fontsize=14)
    fig.tight_layout(rect=[0.025, 0.025, 0.955, 0.955])

    fname = f'{eir_val}_to_pfpr2to10_by_{sweepvar}'
    fig.savefig(os.path.join(wdir, f'{fname}.png'), bbox_extra_artists=(lg,))
    # fig.savefig(os.path.join(wdir, f'{fname}.pdf'), bbox_extra_artists=(lg,))


def input_to_simulated_eir(wdir, emodom, sweepvar='cm_clinical'):
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

    if sweepvar != 'cm_clinical':
        # caption_txt = f'cm_clinical: {np.min(df.cm_clinical)}'
        df = df[(df.cm_clinical == np.min(df.cm_clinical))]

    nx = 1
    ny = len(seasonality)
    f = 1
    firstPlot = True
    fig = plt.figure(figsize=(5, 6))
    for si, season in enumerate(seasonality):
        ax = fig.add_subplot(ny, nx, f);
        f += 1;
        sdf = df[(df.seasonality == season)]
        for p, pdf in sdf.groupby([sweepvar]):
            # plot mean, min and max of seeds and age groups
            xmean = pdf.groupby('eir')['inputEIR'].agg(np.mean)
            ymean = pdf.groupby('eir')['simulatedEIR'].agg(np.mean)
            ymin = pdf.groupby('eir')['simulatedEIR'].agg(np.min)
            ymax = pdf.groupby('eir')['simulatedEIR'].agg(np.max)
            ax.plot(xmean, ymean, '-', linewidth=0.8, label=f"{p}")
            ax.fill_between(xmean, ymin, ymax, alpha=0.3)

        ax.set_ylim(0.1, 100000)
        ax.set_xlim(0.1, 100000)
        ax.set_yscale('symlog')
        ax.set_xscale('symlog')
        if firstPlot: lg = ax.legend(loc="upper left")
        firstPlot = False

    fig.text(0.5, 0.02, 'input annual EIR', ha='center', va='center', fontsize=14)
    fig.text(0.95, 0.75, seasonality[0], ha='center', va='center', rotation=-90, fontsize=14)
    if ny == 2:
        fig.text(0.95, 0.25, seasonality[1], ha='center', va='center', rotation=-90, fontsize=14)
    fig.text(0.06, 0.5, 'simulated annual EIR', ha='right', va='center', rotation='vertical', fontsize=14)
    fig.tight_layout(rect=[0.025, 0.025, 0.955, 0.955])

    fname = f'input_to_simulated_eir_by_{sweepvar}'
    fig.savefig(os.path.join(wdir, f'{fname}.png'), bbox_extra_artists=(lg,))
    # fig.savefig(os.path.join(wdir, f'{fname}.pdf'), bbox_extra_artists=(lg,))


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
    # caption_txt = ''

    if sweepvar != 'cm_clinical':
        # caption_txt = f'cm_clinical: {np.min(df.cm_clinical)}'
        df = df[(df.cm_clinical == np.min(df.cm_clinical))]

    if channel == 'prevalence_2to10' or channel == 'prevalence':
        ylim_up = 1
        ylab = channel.replace('prevalence', '$\it{Pf}$PR$')
    else:
        ylim_up = np.max(df[channel])
        ylab = channel

    nx = 1
    ny = len(emodom)
    f = 1
    firstPlot = True
    fig = plt.figure(figsize=(6, 6))
    for mi, model in enumerate(emodom):
        ax = fig.add_subplot(ny, nx, f);
        f += 1;
        sdf = df[(df.emodom == model)]
        for p, pdf in sdf.groupby([sweepvar]):
            # plot mean, min and max of seeds
            xmean = pdf.groupby('month')['month'].agg(np.mean)
            ymean = pdf.groupby('month')[channel].agg(np.mean)
            ymin = pdf.groupby('month')[channel].agg(np.min)
            ymax = pdf.groupby('month')[channel].agg(np.max)
            ax.plot(xmean, ymean, '-', linewidth=0.8, label=f"{p}")
            ax.fill_between(xmean, ymin, ymax, alpha=0.25)

        ax.set_ylim(0, ylim_up)
        ax.set_xlim(0, 12)
        ax.set_xlabel('month', fontsize=14)
        if firstPlot: lg = ax.legend(loc="upper left", title=sweepvar)  # , title_fontproperties={"weight": "bold"}
        firstPlot = False

    fig.text(0.02, 0.5, ylab, ha='center', va='center', rotation='vertical', fontsize=14)
    fig.text(0.95, 0.75, emodom[0], ha='center', va='center', rotation=-90, fontsize=14)
    if ny == 2:
        fig.text(0.95, 0.25, emodom[1], ha='center', va='center', rotation=-90, fontsize=14)
    fig.tight_layout(rect=[0.023, 0.025, 0.955, 0.955])

    fname = f'monthly_{channel}_by_{sweepvar}_age{agegrp}'
    fig.savefig(os.path.join(wdir, f'{fname}.png'), bbox_extra_artists=(lg,))
    # fig.savefig(os.path.join(wdir, f'{fname}.pdf'), bbox_extra_artists=(lg,))


# Plots by sweeps and channels

def sweep_by_channel_plot(wdir, emodom, x_var, channel, sweepvar, facet_var, agegrp='0-5'):
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
    # if channel == 'prevalence_2to10' or channel == 'prevalence':
    #    ylim_up = 1

    fig, axes = plt.subplots(len(df[facet_var].unique()), 1, sharex=True, figsize=(8, 5 * len(df[facet_var].unique())))
    firstPlot = True

    unique_groups = df[sweepvar].unique()
    unique_facets = df[facet_var].unique()

    num_colors = len(unique_groups)
    num_facets = len(unique_facets)

    color_palette = sns.color_palette('husl', num_colors)

    # Iterate through each facet and plot the lines for each group
    for i, facet_value in enumerate(unique_facets):
        facet_data = df[df[facet_var] == facet_value]
        ax = axes[i] if len(df[facet_var].unique()) > 1 else axes  # Handle single facet

        for p, (group_val, pdf) in enumerate(facet_data.groupby([sweepvar])):
            # plot mean, min and max of seeds
            agg_results = pdf.groupby(x_var)[channel].agg(['mean', 'min', 'max']).reset_index()
            xmean = agg_results[x_var]
            ymean = agg_results['mean']
            ymin = agg_results['min']
            ymax = agg_results['max']
            ax.plot(xmean, ymean, '-', linewidth=0.8, label=f"{group_val}", color=color_palette[p])
            ax.fill_between(xmean, ymin, ymax, alpha=0.25, color=color_palette[p])

        ax.set_ylim(0, ylim_up)
        ax.set_xlabel(x_var)
        ax.set_ylabel(channel)
        ax.set_title(f"{facet_var} = {facet_value}")
        if firstPlot:
            lg = ax.legend(loc="upper left", title=sweepvar)  # , title_fontproperties={"weight": "bold"}
        firstPlot = False

        # Add a new subplot for the next facet
        ax = plt.subplot(num_facets, 1, i)

    # Adjust layout to avoid overlapping
    plt.tight_layout()

    fname = f'{channel}_by_{x_var}_per_{sweepvar}_and_{facet_var}'
    fig.savefig(os.path.join(wdir, f'{fname}.png'), bbox_extra_artists=(lg,))
    # fig.savefig(os.path.join(wdir, f'{fname}.pdf'), bbox_extra_artists=(lg,))


# Plots over time - require PfPR_ClinicalIncidence_mth.csv and PfPR_ClinicalIncidence_yr.csv
def monthly_timeseries(wdir, emodom, channel, sweepvar='emodom', facet_var='ageGroup', agegrp=None):
    df, wdir = get_emodom_df(wdir, emodom, mth=True, timeseries=True)
    if agegrp:
        df = df[(df.ageGroup == agegrp)]
    df['date'] = pd.to_datetime(df['date'])

    if 'cm_clinical' not in [sweepvar, facet_var]:
        df = df[(df.cm_clinical == np.min(df.cm_clinical))]

    if 'seasonality' not in [sweepvar, facet_var]:
        if 'seasonal' in df.seasonality.unique():
            df = df[(df.seasonality == 'seasonal')]

    if 'eir' not in [sweepvar, facet_var]:
        df = df[(df.eir == np.max(df.eir))]

    if 'emodom' not in [sweepvar, facet_var] and len(df['emodom'].unique()) > 1:
        raise ValueError('emodom needs to be specified in plot if results were combined for more than 1 model')

    ylim_up = np.max(df[channel])
    if channel == 'prevalence_2to10' or channel == 'prevalence':
        ylim_up = 1

    fig, axes = plt.subplots(len(df[facet_var].unique()), 1, sharex=True, figsize=(8, 3 * len(df[facet_var].unique())))
    firstPlot = True

    unique_groups = df[sweepvar].unique()
    unique_facets = df[facet_var].unique()

    num_colors = len(unique_groups)
    num_facets = len(unique_facets)

    color_palette = sns.color_palette('husl', num_colors)

    # Iterate through each facet and plot the lines for each group
    for i, facet_value in enumerate(unique_facets):
        facet_data = df[df[facet_var] == facet_value]
        ax = axes[i] if len(df[facet_var].unique()) > 1 else axes  # Handle single facet

        for p, (group_val, pdf) in enumerate(facet_data.groupby([sweepvar])):
            # plot mean, min and max of seeds
            agg_results = pdf.groupby('date')[channel].agg(['mean', 'min', 'max']).reset_index()
            xmean = agg_results['date']
            ymean = agg_results['mean']
            ymin = agg_results['min']
            ymax = agg_results['max']
            ax.plot(xmean, ymean, '-', linewidth=0.8, label=f"{group_val}", color=color_palette[p])
            ax.fill_between(xmean, ymin, ymax, alpha=0.25, color=color_palette[p])

        ax.set_ylim(0, ylim_up)
        ax.set_xlabel('')
        ax.set_ylabel(channel)
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=6))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.set_title(f"{facet_var} = {facet_value}")
        if firstPlot:
            lg = ax.legend(loc="upper left", title=sweepvar)  # , title_fontproperties={"weight": "bold"}
        firstPlot = False

        # Add a new subplot for the next facet
        if i < num_facets - 1:
            ax = plt.subplot(num_facets, 1, i + 1)

    # Adjust layout to avoid overlapping
    plt.tight_layout()

    fname = f'timeseries_monthly_{channel}_by_{sweepvar}_age{agegrp}'
    fig.savefig(os.path.join(wdir, f'{fname}.png'), bbox_extra_artists=(lg,))
    # fig.savefig(os.path.join(wdir, f'{fname}.pdf'), bbox_extra_artists=(lg,))


def annual_timeseries(wdir, emodom, channel, sweepvar='emodom', facet_var='ageGroup', agegrp=None):
    df, wdir = get_emodom_df(wdir, emodom, mth=False, timeseries=True)
    df = df[(df.ageGroup == agegrp)]

    if 'cm_clinical' not in [sweepvar, facet_var]:
        df = df[(df.cm_clinical == np.min(df.cm_clinical))]

    if 'seasonality' not in [sweepvar, facet_var]:
        df = df[(df.seasonality == df['seasonality'].unique()[0])]

    if 'eir' not in [sweepvar, facet_var]:
        df = df[(df.eir == np.max(df.eir))]

    if 'emodom' not in [sweepvar, facet_var] and len(df['emodom'].unique()) > 1:
        raise ValueError('emodom needs to be specified in plot if results were combined for more than 1 model')

    ylim_up = np.max(df[channel])
    if channel == 'prevalence_2to10' or channel == 'prevalence':
        ylim_up = 1

    fig, axes = plt.subplots(len(df[facet_var].unique()), 1, sharex=True, figsize=(8, 3 * len(df[facet_var].unique())))
    firstPlot = True

    unique_groups = df[sweepvar].unique()
    unique_facets = df[facet_var].unique()

    num_colors = len(unique_groups)
    num_facets = len(unique_facets)

    color_palette = sns.color_palette('husl', num_colors)

    # Iterate through each facet and plot the lines for each group
    for i, facet_value in enumerate(unique_facets):
        facet_data = df[df[facet_var] == facet_value]
        ax = axes[i] if len(df[facet_var].unique()) > 1 else axes  # Handle single facet

        for p, (group_val, pdf) in enumerate(facet_data.groupby([sweepvar])):
            # plot mean, min and max of seeds
            agg_results = pdf.groupby('year')[channel].agg(['mean', 'min', 'max']).reset_index()
            xmean = agg_results['year']
            ymean = agg_results['mean']
            ymin = agg_results['min']
            ymax = agg_results['max']
            ax.plot(xmean, ymean, '-', linewidth=0.8, label=f"{group_val}", color=color_palette[p])
            ax.fill_between(xmean, ymin, ymax, alpha=0.25, color=color_palette[p])

        ax.set_ylim(0, ylim_up)
        ax.set_xlabel('Year')
        ax.set_ylabel(channel)
        ax.set_title(f"{facet_var} = {facet_value}")
        if firstPlot:
            lg = ax.legend(loc="upper left", title=sweepvar)  # , title_fontproperties={"weight": "bold"}
        firstPlot = False

        # Add a new subplot for the next facet
        if i < num_facets - 1:
            ax = plt.subplot(num_facets, 1, i + 1)

    # Adjust layout to avoid overlapping
    plt.tight_layout()

    fname = f'timeseries_annual_{channel}_by_{sweepvar}_age{agegrp}'
    fig.savefig(os.path.join(wdir, f'{fname}.png'), bbox_extra_artists=(lg,))
    # fig.savefig(os.path.join(wdir, f'{fname}.pdf'), bbox_extra_artists=(lg,))


def age_curves(wdir, emodom, channel, sweepvar='emodom', facet_var='seasonality'):
    df, wdir = get_emodom_df(wdir, emodom, mth=False, timeseries=True)
    if 'cm_clinical' not in [sweepvar, facet_var]:
        df = df[(df.cm_clinical == np.min(df.cm_clinical))]

    if 'seasonality' not in [sweepvar, facet_var]:
        df = df[(df.seasonality == df['seasonality'].unique()[0])]

    if 'eir' not in [sweepvar, facet_var]:
        df = df[(df.eir == np.max(df.eir))]

    if 'emodom' not in [sweepvar, facet_var] and len(df['emodom'].unique()) > 1:
        raise ValueError('emodom needs to be specified in plot if results were combined for more than 1 model')

    df = df.groupby(['ageGroup','seed',sweepvar, facet_var])[channel].agg(np.mean).reset_index()

    ylim_up = np.max(df[channel])
    if channel == 'prevalence_2to10' or channel == 'prevalence':
        ylim_up = 1

    fig, axes = plt.subplots(len(df[facet_var].unique()), 1, sharex=True, figsize=(5, 3 * len(df[facet_var].unique())))
    firstPlot = True

    unique_groups = df[sweepvar].unique()
    unique_facets = df[facet_var].unique()

    num_colors = len(unique_groups)
    num_facets = len(unique_facets)

    #color_palette = sns.color_palette('husl', num_colors)

    # Iterate through each facet and plot the lines for each group
    for i, facet_value in enumerate(unique_facets):
        facet_data = df[df[facet_var] == facet_value]
        ax = axes[i] if len(df[facet_var].unique()) > 1 else axes  # Handle single facet

        for p, (group_val, pdf) in enumerate(facet_data.groupby([sweepvar])):
            # plot mean, min and max of seeds
            agg_results = pdf.groupby('ageGroup')[channel].agg(['mean', 'min', 'max']).reset_index()
            xmean = agg_results['ageGroup']
            ymean = agg_results['mean']
            ymin = agg_results['min']
            ymax = agg_results['max']
            ax.plot(xmean, ymean, '-', linewidth=0.8, label=f"{group_val}")
            ax.fill_between(xmean, ymin, ymax, alpha=0.25)

            ax.set_ylim(0, ylim_up)
            ax.set_xlabel('Age (years)')
            ax.set_ylabel(channel)
            ax.set_title(f"{facet_var} = {facet_value}")
        if firstPlot:
            lg = ax.legend(loc="upper left")  # , title_fontproperties={"weight": "bold"}
        firstPlot = False

        # Add a new subplot for the next facet
        if i < num_facets - 1:
            ax = plt.subplot(num_facets, 1, i + 1)

    # Adjust layout to avoid overlapping
    plt.tight_layout()

    fname = f'agecurves_{channel}_by_{sweepvar}'
    fig.savefig(os.path.join(wdir, f'{fname}.png'), bbox_extra_artists=(lg,))
    fig.savefig(os.path.join(wdir, f'{fname}.pdf'), bbox_extra_artists=(lg,))


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

    if len(exp.eir) >= 3:
        eir_relationship_plots = True

    if eir_relationship_plots:
        print('#----- Start running pfpr-eir-incidence relationship plots -----#')
        sweepvar = 'emodom'
        eir_to_prevalence2to10(wdir, emodom, sweepvar=sweepvar, eir_val='simulatedEIR')
        # eir_to_prevalence2to10(job_directory, emodom, sweepvar=sweepvar, eir_val='inputEIR')
        input_to_simulated_eir(wdir, emodom, sweepvar=sweepvar)

        channel_list = ['clinical_incidence', 'severe_incidence', 'prevalence']
        ymaxlist = [6, 0.1, 1]
        for c, channel in enumerate(channel_list):
            prevalence2to10_to_incidence(wdir, emodom, channel=channel, y_lim=ymaxlist[c])

        if exp.om_survey_step == '30d' and exp.emod_step != 'burnin':
            channel_list = ['clinical_incidence', 'severe_incidence', 'prevalence', 'simulatedEIR', 'prevalence_2to10']
            sweepvar = 'eir'
            for channel in channel_list:
                monthly_trends(wdir, emodom, channel=channel, sweepvar=sweepvar)

    # Additional standardized plots - timeseries
    if timeseries_plots:
        print('#----- Running timeseries_plots -----#')
        channel_list = ['clinical_incidence', 'severe_incidence', 'prevalence']  # 'simulatedEIR', 'prevalence_2to10'

        sweepvar = 'emodom'
        facet_var = 'eir'
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
