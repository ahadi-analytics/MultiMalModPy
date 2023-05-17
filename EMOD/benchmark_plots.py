import sys, os, re, datetime
import pandas as pd
import numpy as np
import random

## For plotting
import matplotlib as mpl
mpl.use('Agg')
mpl.rcParams['pdf.fonttype'] = 42
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as  sns

def eir_to_prevalence2to10(wdir,  sweepvar ='access'):
    adf = pd.read_csv((os.path.join(wdir, f'EMOD_benchmark.csv')))
    seasonality = list(adf['seasonality'].unique())
    #if 'access' not in adf.columns:
    #  adf.access = -9
    title = ''

    nx = 1 #len(scaffoldNames)
    ny = len(seasonality)
    f=1
    firstPlot = True
    fig = plt.figure(figsize=(8, 8))
   
    for si, season in enumerate(seasonality):
        ax = fig.add_subplot(ny,nx,f); f += 1;
        sdf = adf[(adf.seasonality == season)]
        for p, pdf in sdf.groupby([sweepvar]):
            ages = pdf['age_group'].unique()
    
            # plot mean, min and max of seeds
            xmean = pdf.groupby('eir')['simulatedEIR'].agg(np.mean)
            ymean = pdf.groupby('eir')['prevalence_2to10'].agg(np.mean)
            ymin = pdf.groupby('eir')['prevalence_2to10'].agg(np.min)
            ymax = pdf.groupby('eir')['prevalence_2to10'].agg(np.max)
            ax.plot(xmean, ymean, '-', linewidth=0.8,  label=f"{p}")
            ax.fill_between(xmean, ymin, ymax , alpha=0.3)
            ax.set_ylim(0, 1)
    
        ax.set_ylim(0, 1)
        ax.set_xlim(0, 10000)
        ax.set_xscale('symlog')
        ax.set_ylabel('$\it{Pf}$PR$_{2-10}$ (%)', fontsize=16)
        if firstPlot: lg = ax.legend(loc="upper left", title="access", title_fontproperties={"weight": "bold"})
        firstPlot = False

    fig.text(0.98, 0.75, seasonality[0], ha='center', va='center', rotation=-90, fontsize=16)
    #fig.text(0.98, 0.25, seasonality[1], ha='center', va='center', rotation=-90, fontsize=16)
    fig.text(0.5, 0.02, 'simulated annual EIR', ha='center', va='center', fontsize=16)
    #fig.text(0.02, 0.03, '$\it{Pf}$PR$_{2-10}$ (%)', ha='center', va='center', rotation=90, fontsize=16)
    fig.text(0.02, 0.5, title, ha='center', va='center', rotation='vertical', fontsize=16)
    plt.tight_layout(rect=[0.025, 0.025, 0.985, 0.985])

    fname = f'{wdir}/eir_to_prevalence.pdf'
    fig.savefig(os.path.join(wdir, f'eir_to_prevalence.png'),bbox_extra_artists=(lg,)) #,   bbox_inches='tight'
    fig.savefig(fname,bbox_extra_artists=(lg,)) #   bbox_inches='tight'


        
def plot_eir_pfpr(wdir, sweep_variables, eirchannel='x_Temporary_Larval_Habitat', pfprchannel='prevalence_2to10', emodom = 'EMOD'):
    # seasonality
    #eirchannel = 'x_Temporary_Larval_Habitat'
    #pfprchannel = 'prevalence_2to10' # 'pfpr'
    df = pd.read_csv(os.path.join(wdir, 'PfPR_ClinicalIncidence_yr.csv'))
    sweep_variables = [s for s in sweep_variables if s !=  'Run_Number']
    sweep_variables = [s for s in sweep_variables if s !=  eirchannel]
    
    ### Aggregate years, age, and Run_Number
    try:
      df = df.groupby(sweep_variables + [eirchannel])[[pfprchannel]].agg(np.mean).reset_index()
    except :
      df = df.groupby([eirchannel])[[pfprchannel]].agg(np.mean).reset_index()
      
    fig1 = plt.figure(f'{eirchannel} - {pfprchannel}', figsize=(6, 6))
    fig1.subplots_adjust(hspace=0.5, left=0.08, right=0.97)

    axes = [fig1.add_subplot(1, 1, x + 1) for x in range(1)]
    ax = axes[0]
    ax.set_ylim(0, 1)
    ax.set_xlim(0, 10000)
    ax.set_xscale('symlog')
    ax.set_ylabel(pfprchannel)
    ax.set_xlabel(eirchannel)
    #ax.grid(b=True, which='major', color='#999999', linestyle='-', alpha=0.3)
    if len(sweep_variables) > 0 :
      for p, pdf in df.groupby(sweep_variables):
          ax.plot(pdf[eirchannel], pdf[pfprchannel], '-', linewidth=0.8, label=p)
      lg = axes[-1].legend(title=sweep_variables, bbox_to_anchor=(1.05, 1.0), loc='upper left')
          
      fig1.savefig(os.path.join(wdir, f'EIR_PfPR_{eirchannel}.png'),bbox_extra_artists=(lg,),   bbox_inches='tight')
    else:
        ax.plot(df[eirchannel], df[pfprchannel], '-', linewidth=0.8)
        fig1.savefig(os.path.join(wdir, f'EIR_PfPR_{eirchannel}.png'))

           