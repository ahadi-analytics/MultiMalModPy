import argparse
import pickle
import os
import numpy as np
import pandas as pd
import matplotlib as mpl
import seaborn as sns

# mpl.use('Agg')
import matplotlib.pyplot as plt

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
        default=['EMOD', 'OpenMalaria']
    )

    return parser.parse_args()


def get_emodom_df(wdir, emodom, mth=False):
    """
    Load and combine data from the specified EMOD and/or OpenMalaria benchmark output files.
    Parameters:
        wdir (str): Working directory where the data files are located.
        emodom (str or list of str): Name of models for which result CSVs should be loaded .
        mth (bool, optional): Set to True if the data files have monthly data. Default is False.
    Returns:
        df (DataFrame): Combined DataFrame containing the combined data for the models listed in emodom.
        wdir (str): Updated working directory (if applicable).
    Raises:
        ValueError: If invalid emodom value is specified.
    """
    fname = 'benchmark.csv'
    if mth:
        fname = 'benchmark_mth.csv'

    if 'OpenMalaria' in emodom:
        om_df = pd.read_csv((os.path.join(wdir, f'om/OM_{fname}')))
        om_df['emodom'] = 'OpenMalaria'
        om_df['annual_input_EIR'] = om_df['eir']
    if 'EMOD' in emodom:
        em_df = pd.read_csv((os.path.join(wdir, f'em/EMOD_{fname}')))
        em_df['emodom'] = 'EMOD'
        em_df['annual_input_EIR'] = em_df['inputEIR']

    if 'OpenMalaria' in emodom and 'EMOD' in emodom:
        df = em_df.append(om_df)
        # wdir = os.path.join(wdir, 'comb')
    elif 'OpenMalaria' and not 'EMOD' in emodom:
        wdir = os.path.join(wdir, 'om')
        df = om_df
    elif 'EMOD' and not 'OpenMalaria' in emodom:
        wdir = os.path.join(wdir, 'em')
        df = em_df
    else:
        raise ValueError(f"Please specify emodom as EMOD and/or OpenMalaria (list), {emodom} not valid")

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
            for p, pdf in sdf.groupby(['age_group']):
                ages = pdf['age_group'].unique()

                # plot mean, min and max of seeds
                xvalues = pdf.groupby('annual_input_EIR')['prevalence_2to10'].agg(np.mean)
                ymean = pdf.groupby('annual_input_EIR')[channel].agg(np.mean)
                ymin = pdf.groupby('annual_input_EIR')[channel].agg(np.min)
                ymax = pdf.groupby('annual_input_EIR')[channel].agg(np.max)
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
    #caption_txt = ''

    if sweepvar != 'cm_clinical':
        #caption_txt = f'cm_clinical: {np.min(df.cm_clinical)}'
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
            xmean = pdf.groupby('annual_input_EIR')[eir_val].agg(np.mean)
            ymean = pdf.groupby('annual_input_EIR')['prevalence_2to10'].agg(np.mean)
            ymin = pdf.groupby('annual_input_EIR')['prevalence_2to10'].agg(np.min)
            ymax = pdf.groupby('annual_input_EIR')['prevalence_2to10'].agg(np.max)
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
    #caption_txt = ''

    if sweepvar != 'cm_clinical':
        #caption_txt = f'cm_clinical: {np.min(df.cm_clinical)}'
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
            xmean = pdf.groupby('annual_input_EIR')['inputEIR'].agg(np.mean)
            ymean = pdf.groupby('annual_input_EIR')['simulatedEIR'].agg(np.mean)
            ymin = pdf.groupby('annual_input_EIR')['simulatedEIR'].agg(np.min)
            ymax = pdf.groupby('annual_input_EIR')['simulatedEIR'].agg(np.max)
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


def monthly_trends(wdir, emodom, channel, sweepvar='annual_input_EIR', agegrp='0-5'):
    """
    Generate line plots for monthly trends for channel (yaxis) by sweepvar for selected age groups.
    Note, assumed single occurence per month, i.e. aggregated across years (reads in benchmark_mth.csv)
    Parameters:
        wdir (str): Working directory where the plot will be saved.
        emodom (str or list of str): Name of models for which result dataframes should be loaded.
        channel (str): Variable representing the y-axis data to be plotted.
        sweepvar (str, optional): Variable to group the data and create multiple lines on the plot. Default is 'annual_input_EIR'.
        agegrp (str, optional): Age group filter for the data. Default is '0-5'.
    Returns:
        None (plots are saved to disk).
    Raises:
        ValueError: If no seasonal transmission pattern is specified in the data.
    """
    df, wdir = get_emodom_df(wdir, emodom, mth=True)
    df = df[(df.seasonality == 'seasonal')]
    df = df[(df.age_group == agegrp)]
    if df.empty:
        raise ValueError('No seasonal transmission pattern specified')
    #caption_txt = ''

    if sweepvar != 'cm_clinical':
        #caption_txt = f'cm_clinical: {np.min(df.cm_clinical)}'
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
    df = df[(df.age_group == agegrp)]

    if 'cm_clinical' not in [x_var, channel, sweepvar, facet_var]:
        df = df[(df.cm_clinical == np.min(df.cm_clinical))]

    if 'seasonality' not in [x_var, channel, sweepvar, facet_var]:
        df = df[(df.seasonality == df['seasonality'].unique()[0])]

    if 'annual_input_EIR' not in [x_var, channel, sweepvar, facet_var]:
        df = df[(df.annual_input_EIR == np.max(df.annual_input_EIR))]

    if 'emodom' not in [x_var, channel, sweepvar, facet_var] and len(df['emodom'].unique())>1:
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
            xmean = pdf.groupby(x_var)[x_var].agg(np.mean)
            ymean = pdf.groupby(x_var)[channel].agg(np.mean)
            ymin = pdf.groupby(x_var)[channel].agg(np.min)
            ymax = pdf.groupby(x_var)[channel].agg(np.max)
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
        if i < num_facets - 1:
            ax = plt.subplot(num_facets, 1, i + 1)

    # Adjust layout to avoid overlapping
    plt.tight_layout()

    fname = f'{channel}_by_{x_var}_per_{sweepvar}_and_{facet_var}'
    fig.savefig(os.path.join(wdir, f'{fname}.png'), bbox_extra_artists=(lg,))
    # fig.savefig(os.path.join(wdir, f'{fname}.pdf'), bbox_extra_artists=(lg,))


if __name__ == "__main__":
    args = parse_args()
    job_directory = args.directory
    emodom = args.emodom
    if isinstance(emodom, str):
        emodom = [emodom]

    wdir = job_directory

    if len(emodom) == 2:
        sweepvar = 'emodom'  ## FIXME, when using both model use them as sweepvar only possibility
    if len(emodom) == 1:
        sweepvar = 'cm_clinical'

    prevalence2to10_to_incidence(wdir, emodom, channel='clinical_incidence', y_lim=6)
    prevalence2to10_to_incidence(wdir, emodom, channel='severe_incidence', y_lim=0.1)
    prevalence2to10_to_incidence(wdir, emodom, channel='prevalence', y_lim=1)

    eir_to_prevalence2to10(wdir, emodom, sweepvar=sweepvar, eir_val='simulatedEIR')
    # eir_to_prevalence2to10(job_directory, emodom, sweepvar=sweepvar, eir_val='inputEIR')
    input_to_simulated_eir(wdir, emodom, sweepvar=sweepvar)

    try:
        sweepvar = 'annual_input_EIR'
        monthly_trends(wdir, emodom, channel='prevalence', sweepvar=sweepvar)
        monthly_trends(wdir, emodom, channel='clinical_incidence', sweepvar=sweepvar)
        monthly_trends(wdir, emodom, channel='severe_incidence', sweepvar=sweepvar)
        monthly_trends(wdir, emodom, channel='prevalence_2to10', sweepvar=sweepvar)
        monthly_trends(wdir, emodom, channel='simulatedEIR', sweepvar=sweepvar)
    except:
        print('No monthly plots generated')

    # Additional custom plots
    sweep_plots = False # requires customization depending on variables to select
    if sweep_plots:
        x_var = 'cm_clinical'
        sweepvar = 'annual_input_EIR'
        facet_var = 'emodom'
        sweep_by_channel_plot(wdir, emodom, x_var=x_var, channel='clinical_incidence', sweepvar=sweepvar,  facet_var=facet_var)
        sweep_by_channel_plot(wdir, emodom, x_var=x_var, channel='severe_incidence', sweepvar=sweepvar, facet_var=facet_var)
        sweep_by_channel_plot(wdir, emodom, x_var=x_var, channel='prevalence', sweepvar=sweepvar, facet_var=facet_var)
        sweep_by_channel_plot(wdir, emodom, x_var=x_var, channel='prevalence_2to10', sweepvar=sweepvar, facet_var=facet_var)
        # sweep_by_channel_plot(wdir, emodom, x_var=x_var,channel='simulatedEIR',sweepvar=sweepvar, facet_var= facet_var)
