import os
import argparse
import matplotlib as mpl
import numpy as np
import pandas as pd

mpl.use('Agg')
mpl.rcParams['pdf.fonttype'] = 42
# mpl.rc('font', **{'family': 'sans-serif', 'sans-serif': ['Helvetica']})
# mpl.rc('text', usetex=True)
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker


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
    return parser.parse_args()


def all_age_sample_plot(wdir, sweep_variables, inset_channels, survey_steps=30):
    df = pd.read_csv(os.path.join(wdir, 'All_Age_InsetChart.csv'))
    df['date'] = pd.to_datetime(df['date'])

    ## Aggregate runs/seeds
    df = df.groupby(['date'] + sweep_variables)[inset_channels].agg(np.mean).reset_index()

    for sweep_var in sweep_variables:
        if df[sweep_var].dtype == np.number:
            df[sweep_var] = [round(x, 4) for x in df[sweep_var]]
        else:
            pass

    fig = plt.figure('InsetChart', figsize=(12, 6))
    fig.subplots_adjust(hspace=0.5, left=0.08, right=0.97)
    axes = [fig.add_subplot(3, 5, x + 1) for x in range(15)]

    for ch, channel in enumerate(inset_channels):
        ax = axes[ch]
        for p, pdf in df.groupby(sweep_variables):
            ax.plot(pdf['date'], pdf[channel], '-', linewidth=0.8, label=p)
        ax.set_title(channel)
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=6))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    # if len(sweep_variables) > 0:
    #    axes[-1].legend(title=sweep_variables, loc=7)
    fig.text(0.5, 0.02, 'Time in years', ha='center', va='center', fontsize=12)
    fig.tight_layout(rect=[0.023, 0.025, 0.955, 0.955])
    fig.savefig(os.path.join(wdir, 'InsetChart.png'))


def sample_plot_yr(wdir, sweep_variables, agebin=5):
    channels = ['nHost', 'nUncomp', 'nSevere', 'nInfect', 'nPatent', 'pfpr']
    df = pd.read_csv(os.path.join(wdir, 'OM_surveyoutput_yr.csv'))
    sweep_variables = [s for s in sweep_variables if s != 'seed']
    df['pfpr'] = df['nPatent'] / df['nHost']
    df = df.groupby(['year', 'agebin'] + sweep_variables)[channels].agg(np.mean).reset_index()

    df = df.loc[df['agebin'] == agebin]

    for sweep_var in sweep_variables:
        if df[sweep_var].dtype == np.number:
            df[sweep_var] = [round(x, 4) for x in df[sweep_var]]
        else:
            pass

    fig = plt.figure('PfPR_ClinicalIncidence_yr', figsize=(10, 8))
    fig.subplots_adjust(hspace=0.5, left=0.08, right=0.97)
    fig.suptitle(f'agebin: {agebin}')
    axes = [fig.add_subplot(3, 2, x + 1) for x in range(6)]

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
    # if len(sweep_variables) > 0:
    #     lg = axes[-1].legend(title=sweep_variables, bbox_to_anchor=(1.05, 1.0), loc='upper left')
    fig.savefig(os.path.join(wdir,
                             f'PfPR_ClinicalIncidence_yr_agebin{agebin}.png'))  # ,bbox_extra_artists=(lg,), bbox_inches='tight')


def sample_plot_mth(wdir, sweep_variables, agebin=5):
    channels = ['nHost', 'nUncomp', 'nSevere', 'nInfect', 'nPatent', 'pfpr']
    sweep_variables = [s for s in sweep_variables if s != 'seed']

    df = pd.read_csv(os.path.join(wdir, 'OM_surveyoutput_mth.csv'))
    df['pfpr'] = df['nPatent'] / df['nHost']

    ## Select 2nd last year of simulation
    df = df.loc[df['year'] == np.max(df['year']) - 1]
    df = df.groupby(['survey', 'agebin'] + sweep_variables)[channels].agg(np.mean).reset_index()
    df = df.loc[df['agebin'] == agebin]

    for sweep_var in sweep_variables:
        if df[sweep_var].dtype == np.number:
            df[sweep_var] = [round(x, 4) for x in df[sweep_var]]
        else:
            pass

    fig1 = plt.figure('PfPR_ClinicalIncidence_mth', figsize=(10, 8))
    fig1.subplots_adjust(hspace=0.5, left=0.08, right=0.97)
    fig1.suptitle(f'agebin: {agebin}')
    axes = [fig1.add_subplot(3, 2, x + 1) for x in range(6)]
    for ch, channel in enumerate(channels):
        ax = axes[ch]
        y_lim = np.max(df[channel]) + (np.max(df[channel]) * 0.2)
        ax.set_ylim(0, y_lim)
        for p, pdf in df.groupby(sweep_variables):
            ax.plot(pdf['month'], pdf[channel], '-', linewidth=0.8, label=p)
        ax.set_title(channel)
        # ax.set_ylabel(channel)
    # if len(sweep_variables) > 0:
    #    lg = axes[-1].legend(title=sweep_variables, bbox_to_anchor=(1.05, 1.0), loc='upper left')
    fig1.savefig(os.path.join(wdir,
                              f'PfPR_ClinicalIncidence_mth_agebin{agebin}.png'))  # ,bbox_extra_artists=(lg,), bbox_inches='tight')


if __name__ == "__main__":
    # args = parse_args()
    # job_directory = args.directory
    job_directory = '/projects/b1139/emod-om/simulation_outputs/model_characterization_v0_forcedEIR/test__noburnin/'

    wdir = os.path.join(job_directory, 'om')

    exp_tags = ['seed', 'eir', 'access', 'seasonality']  # FIXME dont hardcode
    channels_inset_chart = ['nHost', 'nInfect', 'nPatent', 'totalInfs', 'totalPatentInf', 'nTreatments', 'nUncomp',
                            'nSevere', 'nSeq', 'nIndDeaths',
                            'nDirDeaths', 'inputEIR', 'simulatedEIR', 'expectedDirectDeaths',
                            'expectedSevere']  # 'expectedIndirectDeaths',

    all_age_sample_plot(wdir, exp_tags, channels_inset_chart, survey_steps=30)
    sample_plot_yr(wdir, exp_tags)
    sample_plot_mth(wdir, exp_tags)
