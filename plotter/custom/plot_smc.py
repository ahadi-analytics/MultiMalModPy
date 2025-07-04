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

from plotter.plot_helper import *



# Plots over time - requires mmmpy_mth.csv
def monthly_smc(wdir, df, channel, sweepvar='model', facet_var='ageGroup',age_groups_aggregates=None, one_year=False):
    """
    Parameters:
        wdir (str): Working directory where the plot will be saved.
        df (pandas dataframe): Dataframe that includes combined model results.
        channel (str): Variable representing the y-axis data to be plotted.
        sweepvar (str, optional): Variable to group the data and create multiple lines on the plot. Default is 'eir'.
        facet_var (str, optional): Variable used to create subplots based on its unique values. Default is 'ageGroup'. (The default should change)
        agegrp (str, optional): Age group filter for the data. Default is '5-10'.
    Right now we are setting the default to only show coverages of 0 and 0.6 in the smc age curves.
    Returns:
        None (plots are saved to disk).
    """

    if age_groups_aggregates is None:
        age_groups_aggregates = ['0-0.5','0.5-1', '1-2', '2-5']

    df = df[df['ageGroup'].isin(age_groups_aggregates)]
    coverages = [0, 0.6]
    if one_year:
        coverages = [0]
    df = df[df['smc_coverage'].isin(coverages)]
    if one_year:
        df = df[df['year']==2000]

    df['date'] = pd.to_datetime(df['date'])
    
    if channel == 'prevalence_2to10':
        ylab = channel.replace('prevalence_2to10', '$\it{Pf}$PR$_{2-10}$ (%)')
    else:
        ylab = channel.replace('_', ' ')
    ylab = ylab + " under 5"
    if 'cm_clinical' not in [sweepvar, facet_var]:
        selected_cm = np.min(df.cm_clinical)
        df = df[(df.cm_clinical == selected_cm)]

    if 'seasonality' not in [sweepvar, facet_var]:
        if 'seasonal' in df.seasonality.unique():
            selected_season = 'seasonal'
        else:
            selected_season = 'perennial'
        df = df[(df.seasonality == selected_season)]

    if 'eir' not in [sweepvar, facet_var]:
        selected_eir = np.max(df.eir)
        df = df[(df.eir == selected_eir)]
    print(facet_var)
    print(df[facet_var].unique())
    if 'model' not in [sweepvar, facet_var] and len(df['model'].unique()) > 1:
        raise ValueError('model needs to be specified in plot if results were combined for more than 1 model')

    df = df.groupby(['seed', sweepvar, facet_var, 'smc_coverage','date'])[channel].agg(np.mean).reset_index()
    unique_facets = df[facet_var].unique()
    unique_facets = np.sort(unique_facets)
    color_palette = sns.color_palette('Dark2', len(df['smc_coverage'].unique()))
    firstPlot = True
    nx = 3
    ny = 1
    # Iterate through each facet and plot the lines for each group
    for ei in unique_facets:
        fig = plt.figure(figsize=(10 * nx, 10 * ny))
        eidf = df[df[facet_var] == ei]
        f = 1
        firstPlot=True
        for i, (m, mdf) in enumerate(eidf.groupby([sweepvar])):
            ax = fig.add_subplot(ny, nx, f)
            f += 1
            max_ylim = []
            for color, smclevel in enumerate(mdf['smc_coverage'].unique()):
                smdf = mdf[mdf['smc_coverage']==smclevel]
                ylim_up = np.max(smdf[channel]) * 1.1
                if channel == 'prevalence' or channel == 'prevalence_2to10':
                    ylim_up = min(ylim_up, 1)
                max_ylim.append(ylim_up)
                xmean, ymean = get_x_y(smdf, 'date', channel, channel)
                xmean = xmean['date']
                merge_df = pd.merge(left=xmean, right=ymean, on='date')
                merge_df.sort_values(by='date', inplace=True)
                ax.plot(merge_df['date'], merge_df[channel], '-', linewidth=1.4, label=f"{int(smclevel*100)}%", color=color_palette[color])
                ax.fill_between(merge_df['date'], merge_df[f'{channel}_min'], merge_df[f'{channel}_max'], alpha=0.1,
                                color=color_palette[color])
            if one_year:
                ax.axvline('2000-01-31', linestyle='--')
                ax.axvline('2000-02-28', linestyle='--')
                ax.axvline('2000-03-28', linestyle='--')
                ax.axvline('2000-04-25', linestyle='--')
                xmax = merge_df.loc[merge_df[channel].idxmax(), 'date']
                ymax = merge_df[channel].max()
                text = f'x = {xmax} , y = {ymax}'
                print(text)
                ax.annotate(text, xy=(xmax,ymax))
            if firstPlot:
                lg = ax.legend(loc='upper left', bbox_to_anchor=(0.5, 1.2))
                firstPlot = False
            ax.set_ylabel(ylab)
            ax.set_ylim(0, max(max_ylim))
            ax.set_xlabel('Year')
            if one_year:
                ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=12))
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m'))
            else:
                ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=8))
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
            ax.set_title(f"{m}: eir {ei}")
        if one_year:
            fname = f'2000_smc_{channel}_for_eir{ei}'
        else:
            fname = f'smc_{channel}_for_eir{ei}'
        fig.savefig(os.path.join(wdir, f'{fname}.png'), bbox_extra_artists=(lg,), bbox_inches='tight')
        plt.close()

def smc_age_curves(wdir, df, channel, sweepvar='model', facet_var='seasonality', age_groups_aggregates=None):
    """
    Parameters:
        wdir (str): Working directory where the plot will be saved.
        df (pandas dataframe): Dataframe that includes combined model results.
        channel (str): Variable representing the y-axis data to be plotted.
        sweepvar (str, optional): Variable to group the data and create multiple lines on the plot. Default is 'modelname'.
        facet_var (str, optional): Variable used to create subplots based on its unique values. Default is 'seasonality'. 
    Right now we are setting the default to only show a coverage of 0.6 in the smc age curves.
    Returns:
        None (plots are saved to disk).
    """
    if age_groups_aggregates is None:
        age_groups_aggregates = ['0-0.5', '0.5-1', '1-2', '2-5', '5-10', '10-15', '15-20', '20-100']

    coverages = [0.6]
    df = df[df['smc_coverage'].isin(coverages)]
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

    if 'modelname' not in [sweepvar, facet_var] and len(df['modelname'].unique()) > 1:
        raise ValueError('modelname needs to be specified in plot if results were combined for more than 1 model')
    df = df.groupby(['ageGroup', 'seed', 'year', sweepvar, facet_var])[channel].agg(np.mean).reset_index()

    firstPlot = True
    unique_facets = df[facet_var].unique()
    unique_facets = sorted(unique_facets)
    color_palette = sns.color_palette('Dark2', len(df[sweepvar].unique()))

    nx = 4
    ny = 2
    for fi in unique_facets:
        f = 1
        fig = plt.figure(figsize=(10*nx,10*ny))
        fdf = df[df[facet_var] == fi]
        fdf = fdf[fdf[channel].notnull()]
        firstPlot=True
        max_ylim = []
        for yr in fdf['year'].unique():
            ax = fig.add_subplot(ny,nx,f)
            f += 1
            yrdf = fdf[fdf['year']==yr]
            for i, (s, sdf) in enumerate(yrdf.groupby([sweepvar])):  
                ylim_up = np.max(sdf[channel])*1.1
                if channel == 'prevalence' or channel == 'prevalence_2to10':
                    ylim_up = min(ylim_up,1) 
                max_ylim.append(ylim_up)
                xmean, ymean = get_x_y(sdf, 'ageGroup', channel, channel)
                xmean = xmean['ageGroup']
                merge_df = pd.merge(left=xmean, right=ymean, on='ageGroup')
                merge_df['ageGroup'] = pd.Categorical(merge_df['ageGroup'], age_groups_aggregates)
                merge_df.sort_values('ageGroup', inplace=True)
                ax.plot(merge_df['ageGroup'], merge_df[channel], '-', linewidth=1.4, label=f"{s}", color=color_palette[i])
                ax.fill_between(merge_df['ageGroup'], merge_df[f'{channel}_min'], merge_df[f'{channel}_max'], alpha=0.1, color=color_palette[i])
            ax.set_title(f"Year: {int(yr)}")
            ax.tick_params(axis='x', labelrotation = 45)
            ax.set_xlabel('Age (years)')
            ax.set_ylabel(ylab)
            if firstPlot:
                lg = ax.legend(loc='upper left', bbox_to_anchor=(0.5, 1.4))
                firstPlot = False
        fname = f'agecurves_{channel}_by_{sweepvar}_eir{fi}'
        ax.set_ylim(0, max(max_ylim))
        fig.suptitle(f'{facet_var}: {fi}, SMC Coverage: 0.6', fontsize=16)
        fig.savefig(os.path.join(wdir, f'{fname}.png'), bbox_extra_artists=(lg,), bbox_inches='tight')
        plt.close()


if __name__ == "__main__":
    args = parse_args()
    out_dir = args.directory
    modelname = args.modelname # ['EMOD', 'OpenMalaria', 'malariasimulation']
    if isinstance(modelname, str):
        modelname = [modelname]
    file = open(os.path.join(out_dir, "exp.obj"), "rb")
    exp = pickle.load(file)

    channel_list = ['clinical_incidence', 'severe_incidence', 'prevalence', 'simulatedEIR', 'prevalence_2to10','n_total_mos_pop']
    sweepvar = 'modelname'
    facet_var = 'ageGroup'

    if len(exp.eir) > 1 & len(exp.eir) <= 3:
        facet_var = 'eir'
    if facet_var == 'ageGroup' and len(exp.cm_clinical) > 1:
        facet_var = 'cm_clinical'
    if facet_var == 'ageGroup' and len(exp.seasonality) > 1:
        facet_var = 'seasonality'

    df_mth, wdir = get_output_df(out_dir, modelname, mth=True)
    df_yr, _ = get_output_df(out_dir, modelname, yr=True)

    if not df_mth.empty:
        for channel in channel_list:
            print(f'#----- Plotting monthly timeseries for {channel}-----#')
            monthly_smc(wdir, df_mth, channel=channel, sweepvar=sweepvar, facet_var=facet_var)

        #monthly_smc(out_dir, modelname, channel='simulatedEIR', sweepvar=sweepvar, facet_var=facet_var, one_year=True)
        #monthly_smc(out_dir, modelname, channel='n_total_mos_pop', sweepvar=sweepvar, facet_var=facet_var, one_year=True)
        #monthly_smc(out_dir, modelname, channel='clinical_incidence', sweepvar=sweepvar, facet_var=facet_var, one_year=True)

    if not df_yr.empty:
        age_groups_aggregates_sub = [x for x in exp.age_groups_aggregates if x not in ([[0, 5], [0, 100]])]
        age_groups_aggregates_sub = ["{}-{}".format(sublist[0], sublist[1]) for sublist in age_groups_aggregates_sub]

        channel_list = ['clinical_incidence', 'severe_incidence', 'prevalence']
        sweepvar = 'modelname'
        facet_var = 'ageGroup'

        if len(exp.eir) > 1 & len(exp.eir) <= 3:
            facet_var = 'eir'
        if facet_var == 'ageGroup' and len(exp.cm_clinical) > 1:
            facet_var = 'cm_clinical'
        if facet_var == 'ageGroup' and len(exp.seasonality) > 1:
            facet_var = 'seasonality'

        for channel in channel_list:
            print(f'#----- Plotting Age Curves for {channel}-----#')
            smc_age_curves(wdir, df_yr, channel=channel, sweepvar=sweepvar, facet_var=facet_var,
                       age_groups_aggregates=age_groups_aggregates_sub)
