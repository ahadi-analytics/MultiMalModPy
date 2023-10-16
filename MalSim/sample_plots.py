import os
import argparse
import matplotlib as mpl
import datetime
import numpy as np
import pandas as pd
import pickle

# mpl.use('Agg')
mpl.rcParams['pdf.fonttype'] = 42
# mpl.rc('font', **{'family': 'sans-serif', 'sans-serif': ['Helvetica']})
# mpl.rc('text', usetex=True)
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker


def parse_args():
    """
    Parses command-line arguments for simulation specifications.
    """
    # Set the description for the argument parser
    description = "Simulation specifications"
    parser = argparse.ArgumentParser(description=description)
    # Add the required argument for the job directory
    parser.add_argument(
        "-d",
        "--directory",
        type=str,
        required=True,
        help="Job Directory where exp.obj is located",
    )
    return parser.parse_args()


def all_age_sample_plot(wdir, sweep_variables, inset_channels, sim_start=2000):
    """
    Generate a sample plot for all age data from the 'All_Age_InsetChart.csv' file.
    Parameters:
    - wdir (str): Working directory.
    - sweep_variables (list): List of sweep variables.
    - inset_channels (list): List of channels for the InsetChart.
    """
    # Read the data from a CSV file
    df = pd.read_csv(os.path.join(wdir, 'daily.csv'))

    df['day'] = df['timestep'] % 365
    df['year'] = df['timestep'].apply(lambda x: int(x / 365) + sim_start)
    df['date'] = df.apply(lambda x: datetime.date(int(x['year']), 1, 1) + datetime.timedelta(int(x['day']) - 1), axis=1)

    # Group the data by date and sweep variables, and calculate the mean of the outcome channels
    inset_channels = [ch for ch in inset_channels if ch in df.columns]
    df = df.groupby(['date'] + sweep_variables)[inset_channels].agg(
        np.mean).reset_index()  ## aggregate age and seeds, taking mean

    # Round numeric sweep variables shown in legend
    for sweep_var in sweep_variables:
        try:
            df[sweep_var] = [round(x, 4) for x in df[sweep_var]]
        except:
            pass

    # Create the plot figure
    fig = plt.figure('InsetChart', figsize=(20, 10))
    fig.subplots_adjust(hspace=0.5, left=0.08, right=0.97)
    axes = [fig.add_subplot(3, 3, x + 1) for x in range(8)]

    # Plot the data for each channel
    for ch, channel in enumerate(inset_channels):
        ax = axes[ch]
        for p, pdf in df.groupby(sweep_variables):
            ax.plot(pdf['date'], pdf[channel], '-', linewidth=0.8, label=p)
        ax.set_title(channel)
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=6))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    # Uncomment the following lines if you want to add a legend
    # if len(sweep_variables) > 0:
    #    axes[-1].legend(title=sweep_variables, loc=7)

    # Add labels and adjust layout
    fig.text(0.5, 0.02, 'Time in years', ha='center', va='center', fontsize=12)
    fig.tight_layout(rect=[0.023, 0.025, 0.955, 0.955])

    # Save the figure as 'InsetChart.png' in the working directory
    fig.savefig(os.path.join(wdir, f'InsetChart.png'))


def sample_plot_yr(wdir, sweep_variables, agebin=5):
    """
    Generate a sample plot for annual  data from PfPR_ClinicalIncidence_yr.csv
    Parameters:
    - wdir (str): Working directory.
    - sweep_variables (list): List of sweep variables.
    - agebin (int): Age bin. Defaults to 5.
    """
    # Outcome channels to plot
    channels = ['nHost', 'nUncomp', 'nSevere', 'nInfect', 'prevalence', 'prevalence_2to10']

    # Read the data from a CSV file
    df = pd.read_csv(os.path.join(wdir, 'PfPR_ClinicalIncidence_yr.csv'))
    sweep_variables = [s for s in sweep_variables if s != 'seed']

    if 'agebin' not in df.columns:
        df['agebin'] = df['ageGroup'].str.split('-').str[1].astype(float)

    # Group and aggregate the data
    channels = [ch for ch in channels if ch in df.columns]
    df = df.groupby(['year', 'agebin'] + sweep_variables)[channels].agg(np.mean).reset_index()

    # Plot only single agebin as specified
    df = df.loc[df['agebin'] == float(agebin)]

    # Round numeric sweep variables shown in legend
    for sweep_var in sweep_variables:
        try:
            df[sweep_var] = [round(x, 4) for x in df[sweep_var]]
        except:
            pass

    # Create the figure and subplots
    fig = plt.figure('PfPR_ClinicalIncidence_yr', figsize=(10, 8))
    # fig.subplots_adjust(hspace=0.2, left=0.08, right=0.97)
    fig.suptitle(f'agebin: {agebin}')
    axes = [fig.add_subplot(3, 2, x + 1) for x in range(6)]

    # Plot the data for each channel
    for ch, channel in enumerate(channels):
        ax = axes[ch]
        y_lim = np.max(df[channel]) + (np.max(df[channel]) * 0.2)
        for p, pdf in df.groupby(sweep_variables):
            ax.plot(pdf['year'], pdf[channel], '-', linewidth=0.8, label=p)
        ax.set_title(channel)
        ax.set_ylim(0, y_lim)
        tick_positions = np.linspace(df['year'].min(), df['year'].max(), 6)
        ax.xaxis.set_major_locator(ticker.FixedLocator(tick_positions))
        ax.xaxis.set_major_formatter(ticker.FormatStrFormatter('%d'))

    # Uncomment the following lines if you want to add a legend
    # if len(sweep_variables) > 0:
    #     lg = axes[-1].legend(title=sweep_variables, bbox_to_anchor=(1.05, 1.0), loc='upper left')
    fig.text(0.02, 0.5, 'Value', ha='center', va='center', rotation='vertical', fontsize=14)
    fig.text(0.5, 0.02, 'Simulation time (years)', ha='center', va='center', fontsize=14)

    # Adjust layout to avoid overlapping
    fig.tight_layout()

    # Additions to savefig call: bbox_extra_artists=(lg,), bbox_inches='tight')
    fig.savefig(os.path.join(wdir, f'PfPR_ClinicalIncidence_yr_agebin{agebin}.png'))


def sample_plot_mth(wdir, sweep_variables, agebin=5):
    """
    Generate a sample plot for monthly data from PfPR_ClinicalIncidence_mth.csv
    Parameters:
    - wdir (str): Working directory.
    - sweep_variables (list): List of sweep variables.
    - agebin (int): Age bin. Defaults to 5.
    """
    # Outcome channels to plot
    channels = ['nHost', 'nUncomp', 'nSevere', 'nInfect', 'prevalence', 'prevalence_2to10']

    # Remove seed from sweep_variables, hence aggregated runs
    sweep_variables = [s for s in sweep_variables if s != 'seed']

    # Read the data from a CSV file
    df = pd.read_csv(os.path.join(wdir, 'PfPR_ClinicalIncidence_mth.csv'))
    df['day'] = 1
    df['date'] = pd.to_datetime(df[['year', 'month', 'day']])

    # Select the second last year of simulation to reduce number of data points to plot on x-axis
    yr = np.max(df['year']) - 1
    df = df.loc[df['year'] == yr]

    if 'agebin' not in df.columns:
        df['agebin'] = df['ageGroup'].str.split('-').str[1].astype(float)

    # Group and aggregate the data
    channels = [ch for ch in channels if ch in df.columns]
    df = df.groupby(['date', 'agebin'] + sweep_variables)[channels].agg(np.mean).reset_index()

    # Plot only single agebin as specified
    df = df.loc[df['agebin'] == float(agebin)]

    # Round numeric sweep variables shown in legend
    for sweep_var in sweep_variables:
        try:
            df[sweep_var] = [round(x, 4) for x in df[sweep_var]]
        except:
            pass

    # Create the figure and subplots
    fig1 = plt.figure('PfPR_ClinicalIncidence_mth', figsize=(12, 10))
    # fig1.subplots_adjust(hspace=0.5, left=0.08, right=0.97)
    fig1.suptitle(f'agebin: {agebin}')
    axes = [fig1.add_subplot(3, 2, x + 1) for x in range(6)]

    # Plot the data for each channel
    for ch, channel in enumerate(channels):
        ax = axes[ch]
        y_lim = np.max(df[channel]) + (np.max(df[channel]) * 0.2)
        for p, pdf in df.groupby(sweep_variables):
            ax.plot(pdf['date'], pdf[channel], '-', linewidth=0.8, label=p)
        ax.set_title(channel)
        # ax.set_ylabel(channel)
        ax.set_ylim(0, y_lim)
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))

    # Uncomment the following lines if you want to add a legend
    # if len(sweep_variables) > 0:
    #    lg = axes[-1].legend(title=sweep_variables, bbox_to_anchor=(1.05, 1.0), loc='upper left')
    fig1.text(0.02, 0.5, 'Value', ha='center', va='center', rotation='vertical', fontsize=14)
    fig1.text(0.5, 0.02, f'Months (single year {yr})', ha='center', va='center', fontsize=14)

    # Adjust layout to avoid overlapping
    fig1.tight_layout()

    # Additions to savefig call: bbox_extra_artists=(lg,), bbox_inches='tight')
    fig1.savefig(os.path.join(wdir, f'PfPR_ClinicalIncidence_mth_agebin{agebin}.png'))


if __name__ == "__main__":
    # Parse command line arguments
    args = parse_args()
    job_directory = args.directory

    file = open(os.path.join(job_directory, "exp.obj"), "rb")
    exp = pickle.load(file)
    sim_start = exp.sim_start_year_om + exp.sim_dur_years - exp.monitoring_years
    # Set wdir directory for loading and saving simulation results (for EMOD)
    wdir = os.path.join(job_directory, 'MalSim')

    # Determine whether simulation ran with forced or dynamic EIR and set eirchannel
    # Define tags and channels for sample plots
    #exp_tags = [x for x in exp.sweep_list if x != 'seed']  # + ['seed']
    exp_tags = ['index'] #TODO, add scenarios to daily?
    channels_inset_chart = ['nPopulation', 'nHost', 'prevalence',
                            'incidence', 'clinical_incidence',
                            'severe_incidence', 'prevalence_2to10','EIR_gamb']

    # Create sample plots
    all_age_sample_plot(wdir, exp_tags, channels_inset_chart, sim_start=sim_start)
    sample_plot_yr(wdir, exp_tags)
    sample_plot_mth(wdir, exp_tags)
