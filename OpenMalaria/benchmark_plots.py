import os

# from helper import *
## For plotting
import matplotlib as mpl
import numpy as np
import pandas as pd

mpl.use('Agg')
import matplotlib.pyplot as plt

mpl.rcParams['pdf.fonttype'] = 42


# rc('font',**{'family':'sans-serif','sans-serif':['Helvetica']})
# rc('text', usetex=True)

def prevalence2to10_to_incidence(wdir, channel='clinical_incidence', y_lim=6):
    adf = pd.read_csv((os.path.join(wdir, f'OM_benchmark.csv')))
    seasonality = list(adf['seasonality'].unique())
    title = f'{channel.replace("_", " ").capitalize()} (events per person per year)'

    nx = 1  # len(scaffoldNames)
    ny = len(seasonality)
    f = 1
    firstPlot = True
    fig = plt.figure(figsize=(8, 8))
    # for each age group, plot x = prevalence 2_to_10, y = incidences

    for si, season in enumerate(seasonality):
        ax = fig.add_subplot(ny, nx, f);
        f += 1;
        sdf = adf[(adf.seasonality == season)]
        for p, pdf in sdf.groupby(['age_group']):
            ages = pdf['age_group'].unique()

            # plot mean, min and max of seeds
            xvalues = pdf.groupby('eir')['prevalence_2to10'].agg(np.mean)
            ymean = pdf.groupby('eir')[channel].agg(np.mean)
            ymin = pdf.groupby('eir')[channel].agg(np.min)
            ymax = pdf.groupby('eir')[channel].agg(np.max)
            ax.plot(xvalues, ymean, marker='o', label=ages if firstPlot else "")
            ax.fill_between(xvalues, ymin, ymax, alpha=0.3)

        ax.set_ylim(0, y_lim)
        ax.set_xlim(0, 100)
        ax.set_xticks([0, 20, 40, 60, 80, 100])
        # ax.set_xticklabels([str(i) + '%' for i in [0, 20, 40, 60, 80, 100]])
        if firstPlot: ax.legend(loc="upper left", title="age groups", title_fontproperties={"weight": "bold"})
        firstPlot = False

    fig.text(0.98, 0.75, seasonality[0], ha='center', va='center', rotation=-90, fontsize=16)
    fig.text(0.98, 0.25, seasonality[1], ha='center', va='center', rotation=-90, fontsize=16)
    fig.text(0.5, 0.02, '$\it{Pf}$PR$_{2-10}$ (%)', ha='center', va='center', fontsize=16)
    fig.text(0.02, 0.5, title, ha='center', va='center', rotation='vertical', fontsize=16)
    plt.tight_layout(rect=[0.025, 0.025, 0.985, 0.985])

    fname = f'{wdir}/age_pfpr_to_{channel}.pdf'
    fig.savefig(fname)


def eir_to_prevalence2to10(wdir, sweepvar='access'):
    adf = pd.read_csv((os.path.join(wdir, f'OM_benchmark.csv')))
    seasonality = list(adf['seasonality'].unique())
    # if 'access' not in adf.columns:
    #  adf.access = -9
    title = ''

    nx = 1  # len(scaffoldNames)
    ny = len(seasonality)
    f = 1
    firstPlot = True
    fig = plt.figure(figsize=(8, 8))

    for si, season in enumerate(seasonality):
        ax = fig.add_subplot(ny, nx, f);
        f += 1;
        sdf = adf[(adf.seasonality == season)]
        for p, pdf in sdf.groupby([sweepvar]):
            ages = pdf['age_group'].unique()

            # plot mean, min and max of seeds
            xmean = pdf.groupby('eir')['simulatedEIR'].agg(np.mean)
            ymean = pdf.groupby('eir')['prevalence_2to10'].agg(np.mean)
            ymin = pdf.groupby('eir')['prevalence_2to10'].agg(np.min)
            ymax = pdf.groupby('eir')['prevalence_2to10'].agg(np.max)
            ax.plot(xmean, ymean / 100, '-', linewidth=0.8, label=f"{p}")
            ax.fill_between(xmean, ymin / 100, ymax / 100, alpha=0.3)
            ax.set_ylim(0, 1)

        ax.set_ylim(0, 1)
        # ax.set_xscale('symlog')
        # ax.set_xlabel('simulated annual EIR')
        ax.set_ylabel('$\it{Pf}$PR$_{2-10}$ (%)', fontsize=16)
        if firstPlot: lg = ax.legend(loc="upper left", title="access", title_fontproperties={"weight": "bold"})
        firstPlot = False

    fig.text(0.98, 0.75, seasonality[0], ha='center', va='center', rotation=-90, fontsize=16)
    fig.text(0.98, 0.25, seasonality[1], ha='center', va='center', rotation=-90, fontsize=16)
    fig.text(0.5, 0.02, 'simulated annual EIR', ha='center', va='center', fontsize=16)
    # fig.text(0.02, 0.03, '$\it{Pf}$PR$_{2-10}$ (%)', ha='center', va='center', rotation=90, fontsize=16)
    fig.text(0.02, 0.5, title, ha='center', va='center', rotation='vertical', fontsize=16)
    plt.tight_layout(rect=[0.025, 0.025, 0.985, 0.985])

    fname = f'{wdir}/eir_to_prevalence.pdf'
    fig.savefig(os.path.join(wdir, f'eir_to_prevalence.png'), bbox_extra_artists=(lg,))  # ,   bbox_inches='tight'
    fig.savefig(fname, bbox_extra_artists=(lg,))  # bbox_inches='tight'
