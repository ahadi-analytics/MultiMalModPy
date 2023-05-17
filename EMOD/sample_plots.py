import os

## For plotting
import matplotlib as mpl
import numpy as np
import pandas as pd

mpl.use('Agg')
mpl.rcParams['pdf.fonttype'] = 42
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def all_age_sample_plot(wdir, sweep_variables, inset_channels):
    df = pd.read_csv(os.path.join(wdir, 'All_Age_InsetChart.csv'))
    df['date'] = pd.to_datetime(df['date'])
    df = df.groupby(['date'] + sweep_variables)[inset_channels].agg(np.mean).reset_index()

    for sweep_var in sweep_variables:
        df[sweep_var] = [round(x, 4) for x in df[sweep_var]]

    fig1 = plt.figure('InsetChart', figsize=(12, 6))
    fig1.subplots_adjust(hspace=0.5, left=0.08, right=0.97)
    fig1.suptitle(f'Analyzer: InsetChartAnalyzer')
    axes = [fig1.add_subplot(3, 5, x + 1) for x in range(15)]

    for ch, channel in enumerate(inset_channels):
        ax = axes[ch]
        for p, pdf in df.groupby(sweep_variables):
            ax.plot(pdf['date'], pdf[channel], '-', linewidth=0.8, label=p)
        ax.set_title(channel)
        # ax.set_ylabel(channel)
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=12))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%y'))
    if len(sweep_variables) > 0:
        axes[-1].legend(title=sweep_variables, loc=7)
    fig1.tight_layout()
    fig1.savefig(os.path.join(wdir, 'InsetChart.png'))


def sample_plot_yr(wdir, sweep_variables, agebin=5):
    channels = ['nHost', 'nUncomp_annualized', 'nSevere_annualized', 'nInfect', 'pfpr', 'prevalence_2to10']
    df = pd.read_csv(os.path.join(wdir, 'PfPR_ClinicalIncidence_yr.csv'))
    sweep_variables = [s for s in sweep_variables if s != 'Run_Number']
    df = df.groupby(['year', 'age'] + sweep_variables)[channels].agg(np.mean).reset_index()

    df = df.loc[df['age'] == agebin]

    for sweep_var in sweep_variables:
        df[sweep_var] = [round(x, 4) for x in df[sweep_var]]

    fig1 = plt.figure('PfPR_ClinicalIncidence_yr', figsize=(10, 8))
    fig1.subplots_adjust(hspace=0.5, left=0.08, right=0.97)
    fig1.suptitle(f'agebin: {agebin}')
    axes = [fig1.add_subplot(3, 2, x + 1) for x in range(6)]

    for ch, channel in enumerate(channels):
        ax = axes[ch]
        for p, pdf in df.groupby(sweep_variables):
            ax.plot(pdf['year'], pdf[channel], '-', linewidth=0.8, label=p)
        ax.set_title(channel)
        # ax.set_ylabel(channel)
        # ax.xaxis.set_ticks(np.arange(0, 13, 1))
    if len(sweep_variables) > 0:
        lg = axes[-1].legend(title=sweep_variables, bbox_to_anchor=(1.05, 1.0), loc='upper left')

    fig1.savefig(os.path.join(wdir, f'PfPR_ClinicalIncidence_yr_agebin{agebin}.png'),
                 bbox_extra_artists=(lg,), bbox_inches='tight')


def sample_plot_mth(wdir, sweep_variables, agebin=5):
    channels = ['nHost', 'nUncomp_annualized', 'nSevere_annualized', 'nInfect', 'pfpr', 'prevalence_2to10']
    df = pd.read_csv(os.path.join(wdir, 'PfPR_ClinicalIncidence_mth.csv'))
    df['day'] = 1
    df['date'] = pd.to_datetime(df[['year', 'month', 'day']])
    sweep_variables = [s for s in sweep_variables if s != 'Run_Number']
    df = df.groupby(['date', 'age'] + sweep_variables)[channels].agg(np.mean).reset_index()

    df = df.loc[df['age'] == agebin]

    for sweep_var in sweep_variables:
        df[sweep_var] = [round(x, 4) for x in df[sweep_var]]

    fig1 = plt.figure('PfPR_ClinicalIncidence_mth', figsize=(10, 8))
    fig1.subplots_adjust(hspace=0.5, left=0.08, right=0.97)
    fig1.suptitle(f'agebin: {agebin}')
    axes = [fig1.add_subplot(3, 2, x + 1) for x in range(6)]
    for ch, channel in enumerate(channels):
        ax = axes[ch]
        for p, pdf in df.groupby(sweep_variables):
            ax.plot(pdf['date'], pdf[channel], '-', linewidth=0.8, label=p)
        ax.set_title(channel)
        # ax.set_ylabel(channel)
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=12))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    if len(sweep_variables) > 0:
        lg = axes[-1].legend(title=sweep_variables, bbox_to_anchor=(1.05, 1.0), loc='upper left')
    fig1.savefig(os.path.join(wdir, f'PfPR_ClinicalIncidence_mth_agebin{agebin}.png'),
                 bbox_extra_artists=(lg,), bbox_inches='tight')
