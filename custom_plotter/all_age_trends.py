import argparse
import os

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


def all_age_sample_plot(wdir, sweep_variables, inset_channels, seasonality):
    df_em = pd.read_csv(os.path.join(wdir, 'em', 'All_Age_InsetChart.csv'))
    df_em['date'] = pd.to_datetime(df_em['date'])
    df_em = df_em.groupby(['date'] + sweep_variables['EMOD'])[inset_channels['EMOD']].agg(np.mean).reset_index()
    df_em['emodom'] = 'EMOD'
    df_em = df_em.rename(columns={'Run_Number': 'seed', 'EIR_scale_factor': 'eir',
                                  'cm_clinical_U5': 'access'})

    df_om = pd.read_csv(os.path.join(wdir, 'om', 'All_Age_InsetChart.csv'))
    df_om['date'] = pd.to_datetime(df_om['date'])
    df_om = df_om.groupby(['date'] + sweep_variables['OpenMalaria'])[inset_channels['OpenMalaria']].agg(
        np.mean).reset_index()
    df_om['True Prevalence'] = df_om['totalPatentInf'] / df_om['nHost']
    df_om['Blood Smear Parasite Prevalence'] = df_om['nPatent'] / df_om['nHost']
    df_om = df_om.rename(columns={'nHost': 'Statistical Population', 'nInfect': 'New Infections',
                                  'nUncomp': 'New Clinical Cases', 'nSevere': 'New Severe Cases'})
    inset_channels['OpenMalaria'] = ['nHost', 'nInfect','totalPatentInf / nHost',  'nPatent / nHost', 'nUncomp', 'nSevere']


    df_om['emodom'] = 'OpenMalaria'
    df_om = df_om[list(df_em.columns)]
    df = pd.concat([df_om, df_em])
    df = df[df['seasonality'] == seasonality]
    df.to_csv(os.path.join(wdir, 'comb','All_Age_InsetChart.csv'), index=False)
    #df = pd.read_csv(os.path.join(wdir, 'comb','All_Age_InsetChart.csv'))
    
    df['date'] = pd.to_datetime(df['date'])
    reference_date = pd.to_datetime(np.min(df['date']))
    df['days'] = (df['date'] - reference_date).dt.days
    df['days'] = df['days']/365
    #df['year'] = df['date'].dt.year
    #df = df[df['year'] > np.min(df['year']) + 1]  ## remove first 2 years

    for sweep_var in sweep_variables['OpenMalaria']:
        if np.issubdtype(df[sweep_var].dtype, np.number):
            df[sweep_var] = [round(x, 4) for x in df[sweep_var]]
        else:
            pass

    for i, (ch_em, ch_om) in enumerate(zip(inset_channels['EMOD'], inset_channels['OpenMalaria'])):
        fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(10, 5))
        fig.subplots_adjust(hspace=0.5, left=0.08, right=0.97)


        for i, emodom in enumerate(df['emodom'].unique()):
            sub_df = df[df['emodom'] == emodom]
            channel_lbl = ch_em
            if emodom == 'OpenMalaria':
                channel_lbl = ch_om

            ax = axes[i]
            for p, pdf in sub_df.groupby('eir'):
                ax.plot(pdf['days'], pdf[ch_em], '-', linewidth=0.8, label=p)
                
            ax.set_title(emodom, fontsize=14)
            ax.set_ylabel(channel_lbl, fontsize=14)
            
            #ax.set_ylim(0, df[ch_em].max() + (df[ch_em].max() * 0.2))
            #ax.set_xlim(df['date'].min(), df['date'].max())
            #ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=6))
            #ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
            tick_positions = np.linspace(pdf['days'].min(), df['days'].max(), 6)
            ax.xaxis.set_major_locator(ticker.FixedLocator(tick_positions))
            ax.xaxis.set_major_formatter(ticker.FormatStrFormatter('%d'))
        

        if ch_em !='Statistical Population':
            axes[-1].legend(title='eir', loc=7)
        fig.text(0.5, 0.02, 'Simulation time (years)', ha='center', va='center', fontsize=12)
        fig.tight_layout(rect=[0.023, 0.025, 0.955, 0.955])
        fig.savefig(os.path.join(wdir, 'comb', f'allAge_timetrend_{ch_em}.png'))
        #fig.savefig(os.path.join(wdir, 'comb','pdf', f'allAge_timetrend_{ch_em}.pdf'))
        
if __name__ == "__main__":

    run_batch = False
    if run_batch:
        args = parse_args()
        job_directory = args.directory
    else:
        #job_directory = '/projects/b1139/emod-om/simulation_outputs/forcedEIR/test_human_demography_noCM_fewEIR_burnin30/'
        job_directory = '/projects/b1139/emod-om/simulation_outputs/model_characterization_v0_forcedEIR/test__noburnin/'
        #job_directory = "C:/Users/mrm9534/NU Malaria Modeling Dropbox/projects/EMOD_OM/simulation_outputs/model_characterization_v0_forcedEIR/test__noburnin"

    wdir = os.path.join(job_directory)

    if 'dynamic' in job_directory:
        eirchannel = "x_Temporary_Larval_Habitat"
    else:
        eirchannel = "EIR_scale_factor"

    exp_tags_em = [eirchannel, 'cm_clinical_U5', 'seasonality']
    exp_tags_om = ['eir', 'access', 'seasonality']

    channels_inset_chart_em = ['Statistical Population', 'New Infections',  'True Prevalence', 'Blood Smear Parasite Prevalence',
                               'New Clinical Cases', 'New Severe Cases']

    channels_inset_om = ['nHost', 'nInfect',  'totalPatentInf','nPatent', 'nUncomp', 'nSevere']

    channels = {'EMOD': channels_inset_chart_em, 'OpenMalaria': channels_inset_om}
    exp_tags = {'EMOD': exp_tags_em, 'OpenMalaria': exp_tags_om}

    all_age_sample_plot(wdir, exp_tags, channels, seasonality='perennial')
