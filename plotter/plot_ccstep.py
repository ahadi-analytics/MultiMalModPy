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


# Plots daily_timeseries - requires PfPR_ClinicalIncidence_daily.csv
def daily_timeseries(fdir, df_all, channel_list, sweepvar='modelname', facet_var='ageGroup', agegrp='5-10'):
    """
    Parameters:
        fdir (str): Directory where the plot will be saved.
        df_all (pandas dataframe): Dataframe that includes combined model results.
        channel (str): Variable representing the y-axis data to be plotted.
        sweepvar (str, optional): Variable to group the data and create multiple lines on the plot. Default is 'modelname'.
        facet_var (str, optional): Variable used to create subplots based on its unique values. Default is 'ageGroup'. (The default should change)
        agegrp (str, optional): Age group filter for the data. Default is '5-10'.
    Returns:
        None (plots are saved to disk).
    """
    df_all = df_all[df_all['timestep'] >= 1460]  # remove the first 4 years of the 55 year monitoring period
    df_all['day_date'] = df_all['timestep'].apply(convert_to_date)

    for seasonality in df_all['seasonality'].unique():
        dfs = df_all[df_all['seasonality']==seasonality]
        for cm in dfs['cm_clinical'].unique():
            dfc = dfs[dfs['cm_clinical']==cm]
            for channel in channel_list:
                print(f'#----- Plotting daily timeseries for {channel}-----#')
                if channel == 'prevalence_2to10':
                    ylab = channel.replace('prevalence_2to10', '$\it{Pf}$PR$_{2-10}$ (%)')
                else:
                    ylab = channel.replace('_', ' ')

                if facet_var != 'ageGroup' and agegrp is not None:
                    df = dfc[(dfc.ageGroup == agegrp)]

                if agegrp is None:
                    print('Warning: agegrp is set to None, it will combine all ages, please check your age aggregation')
                    # df = dfc.groupby(['day_date', sweepvar, facet_var])[channel].agg(np.mean).reset_index()
                    df = dfc.groupby(['day_date', sweepvar, facet_var, 'target_output_values','cc_change'])[channel].agg(np.mean).reset_index()

                if 'modelname' not in [sweepvar, facet_var] and len(df['modelname'].unique()) > 1:
                    raise ValueError('modelname needs to be specified in plot if results were combined for more than 1 model')

                unique_facets = df[facet_var].unique()
                unique_facets = np.sort(unique_facets)
                color_palette = sns.color_palette('colorblind', max(len(df[sweepvar].unique()),4))
                firstPlot = True
                nx = 2
                ny = 3
                f = 1
                fig = plt.figure(figsize=(10 * nx, 10 * ny))
                # Iterate through each facet and plot the lines for each group
                for ii, (facet, facet_df) in enumerate(df.groupby([facet_var])):
                    ax = fig.add_subplot(ny, nx, f)
                    f += 1
                    max_ylim = []
                    for i, model in enumerate(facet_df[sweepvar].unique()):
                        model_df = facet_df[facet_df[sweepvar] == model]
                        color_key = color_selector(i, model)
                        xmean, ymean = get_x_y(model_df, 'day_date', channel, channel)
                        xmean = xmean['day_date']
                        merge_df = pd.merge(left=xmean, right=ymean, on='day_date')
                        merge_df.sort_values(by='day_date', inplace=True)
                        ax.plot(merge_df['day_date'], merge_df[channel], '-', linewidth=0.8, label=f"{model}",
                                color=color_palette[color_key])
                        x_min_note = merge_df.loc[merge_df['day_date'] == min(merge_df['day_date'])][channel].iloc[0]
                        x_max_note = merge_df.loc[merge_df['day_date'] == max(merge_df['day_date'])][channel].iloc[0]
                        year_factor = max(int((max(merge_df['day_date']).year - min(merge_df['day_date']).year) / 8), 1)
                        ax.annotate(f"{round(x_min_note, 2)}", xy=(min(merge_df['day_date']), x_min_note),
                                    xytext=(min(merge_df['day_date']), x_min_note - int(x_min_note / 10)))
                        ax.annotate(f"{round(x_max_note, 2)}", xy=(max(merge_df['day_date']), x_max_note), xytext=(
                        max(merge_df['day_date']) - pd.DateOffset(years=year_factor), x_max_note - int(x_min_note / 15)))
                        ylim_up = np.max(ymean[channel]) * 1.01
                        if channel == 'prevalence' or channel == 'prevalence_2to10':
                            ylim_up = 1
                        max_ylim.append(ylim_up)
                    if channel == 'prevalence_2to10':
                        print(facet_df['target_output_values'].iloc[0])
                        ax.axhline(facet_df['target_output_values'].iloc[0], linestyle='--')
                        ax.axhline(facet_df['cc_change'].iloc[0], linestyle='--')
                    if firstPlot:
                        lg = ax.legend(loc='upper left', bbox_to_anchor=(0.5, 1.4))
                        # lg = ax.legend(loc='upper left', bbox_to_anchor=(1,0.7))
                        firstPlot = False

                    ax.set_ylabel(ylab)
                    ax.set_ylim(0, max(max_ylim))
                    ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=8))
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
                    ax.set_xlabel('Year')
                    ax.set_title('$\it{Pf}$PR$_{2-10}$' + f': {facet}')
                fname = f'timeseries_daily_{seasonality}_cm{cm}_{channel}_{agegrp}_by_{sweepvar}'
                fig.savefig(os.path.join(fdir, f'{fname}.png'), bbox_extra_artists=(lg,), bbox_inches='tight')
                plt.close()


# Plots daily_timeseries_by_seed - requires PfPR_ClinicalIncidence_daily.csv
def daily_timeseries_by_seed(fdir, df_all, channel_list, sweepvar='modelname', facet_var='ageGroup', agegrp='0-100'):
    """
    Parameters:
        fdir (str): Directory where the plot will be saved.
        df_all (pandas dataframe): Dataframe that includes combined model results.
        channel (str): Variable representing the y-axis data to be plotted.
        sweepvar (str, optional): Variable to group the data and create multiple lines on the plot. Default is 'modelname'.
        facet_var (str, optional): Variable used to create subplots based on its unique values. Default is 'ageGroup'. (The default should change)
        agegrp (str, optional): Age group filter for the data. Default is '5-10'.
    Returns:
        None (plots are saved to disk).
    """

    df_all = df_all[df_all['timestep'] >= 1460]  # remove the first 4 years of the 55 year monitoring period
    df_all['day_date'] = df_all['timestep'].apply(convert_to_date)
    reductions = [f'25%-10%', f'50%-10%', f'50%-25%']
    df_all = df_all[df_all['cc_title'].isin(reductions)]
    for channel in channel_list:
        print(f'#----- Plotting daily timeseries for {channel}-----#')
        if channel == 'prevalence_2to10':
            ylab = channel.replace('prevalence_2to10', '$\it{Pf}$PR$_{2-10}$ (%)')
        else:
            ylab = channel.replace('_', ' ')

        if facet_var != 'ageGroup' and agegrp is not None:
            df = df_all[(df_all.ageGroup == agegrp)]

        if agegrp is None:
            print('Warning: agegrp is set to None, it will combine all ages, please check your age aggregation')
            # df = df_all.groupby(['day_date', sweepvar, facet_var])[channel].agg(np.mean).reset_index()
            df = df_all.groupby(['day_date', sweepvar, facet_var, 'seed'])[channel].agg(np.mean).reset_index()

        if 'modelname' not in [sweepvar, facet_var] and len(df['modelname'].unique()) > 1:
            raise ValueError('modelname needs to be specified in plot if results were combined for more than 1 model')

        unique_facets = df[facet_var].unique()
        unique_facets = np.sort(unique_facets)
        color_palette = sns.color_palette('colorblind', max(len(df['seed'].unique())),4)
        nx = 2
        ny = 3
        f = 1
        lower_prevalence = [0.25, 0.5, 0.5]
        upper_prevalence = [0.1, 0.1, 0.25]
        # Iterate through each facet and plot the lines for each group
        for m, model in enumerate(df[sweepvar].unique()):
            model_df = df[df[sweepvar] == model]
            fig = plt.figure(figsize=(10 * nx, 10 * ny))
            f = 1
            for i, (facet, facet_df) in enumerate(model_df.groupby([facet_var])):
                ax = fig.add_subplot(ny, nx, f)
                f = f + 1
                for si, (seeds, sdf) in enumerate(facet_df.groupby(['seed'])):
                    xmean, ymean = get_x_y(sdf, 'day_date', channel, channel)
                    if model == 'OpenMalaria' and channel == 'simulatedEIR':
                        ymean[channel] = ymean[channel] / 5
                        ymean[f'{channel}_min'] = ymean[f'{channel}_min'] / 5
                        ymean[f'{channel}_max'] = ymean[f'{channel}_max'] / 5
                    xmean = xmean['day_date']
                    merge_df = pd.merge(left=xmean, right=ymean, on='day_date')
                    merge_df.sort_values(by='day_date', inplace=True)
                    ax.plot(merge_df['day_date'], merge_df[channel], '-', linewidth=0.5, label=f"{si}",
                            color=color_palette[m])
                    x_min_note = merge_df.loc[merge_df['day_date'] == min(merge_df['day_date'])][channel].iloc[0]
                    x_max_note = merge_df.loc[merge_df['day_date'] == max(merge_df['day_date'])][channel].iloc[0]
                    year_factor = max(int((max(merge_df['day_date']).year - min(merge_df['day_date']).year) / 8), 1)
                    ax.annotate(f"{round(x_min_note, 2)}", xy=(min(merge_df['day_date']), x_min_note),
                                xytext=(min(merge_df['day_date']), x_min_note - int(x_min_note / 10)))
                    ax.annotate(f"{round(x_max_note, 2)}", xy=(max(merge_df['day_date']), x_max_note), xytext=(
                    max(merge_df['day_date']) - pd.DateOffset(years=year_factor), x_max_note - int(x_min_note / 15)))
                if channel == 'prevalence' or channel == 'prevalence_2to10':
                    ax.axhline(lower_prevalence[i], linestyle='--')
                    ax.axhline(upper_prevalence[i], linestyle='--')
                ax.set_ylabel(ylab)
                ax.set_ylim(-0.1, upper_prevalence[i]+0.1)
                ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=8))
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
                ax.set_xlabel('Year')
                ax.set_title(f'{model}: {facet}')
            fname = f'timeseries_daily_{channel}_{agegrp}_by_{model}_by_seed'
            fig.savefig(os.path.join(fdir, f'{fname}_zoomedin.png'), bbox_inches='tight')
            # fig.savefig(os.path.join(fdir, f'{fname}.pdf'), bbox_inches='tight')
            plt.close()


# Plots daily_vectors - requires PfPR_ClinicalIncidence_daily.csv
def daily_vectors(fdir, df_all, channel, sweepvar='modelname', facet_var='ageGroup', agegrp='0-100'):
    """
    Parameters:
        fdir (str): Directory where the plot will be saved.
        df_all (pandas dataframe): Dataframe that includes combined model results.
        channel (str): Variable representing the y-axis data to be plotted.
        sweepvar (str, optional): Variable to group the data and create multiple lines on the plot. Default is 'modelname'.
        facet_var (str, optional): Variable used to create subplots based on its unique values. Default is 'ageGroup'. (The default should change)
        agegrp (str, optional): Age group filter for the data. Default is '5-10'.
    Returns:
        None (plots are saved to disk).
    """

    df_all = df_all[df_all['timestep'] >= 1460]
    df_all['day_date'] = df_all['timestep'].apply(convert_to_date)

    ylab = channel.replace('_', ' ')

    if facet_var != 'ageGroup' and agegrp is not None:
        df = df_all[(df_all.ageGroup == agegrp)]

    if agegrp is None:
        print('Warning: agegrp is set to None, it will combine all ages, please check your age aggregation')
        df = df_all.groupby(['day_date', sweepvar, facet_var])[channel].agg(np.mean).reset_index()

    if 'modelname' not in [sweepvar, facet_var] and len(df['modelname'].unique()) > 1:
        raise ValueError('modelname needs to be specified in plot if results were combined for more than 1 model')

    unique_facets = df[facet_var].unique()
    unique_facets = np.sort(unique_facets)
    color_palette = sns.color_palette('colorblind', max(len(df[sweepvar].unique())),4)
    firstPlot = True
    nx = 2
    ny = 3
    f = 1

    # Iterate through each facet and plot the lines for each group
    for zz, ii in enumerate(df[sweepvar].unique()):
        fig = plt.figure(figsize=(10 * nx, 10 * ny))
        f = 1
        sdf = df[df[sweepvar] == ii]
        for i, (fi, fdf) in enumerate(sdf.groupby([facet_var])):
            ax = fig.add_subplot(ny, nx, f)
            f += 1
            xmean, ymean = get_x_y(fdf, 'day_date', channel, channel)
            xmean = xmean['day_date']
            merge_df = pd.merge(left=xmean, right=ymean, on='day_date')
            merge_df.sort_values(by='day_date', inplace=True)

            ax.plot(merge_df['day_date'], merge_df[channel], '-', linewidth=0.8, label=f"{fi}", color=color_palette[zz])
            ax.fill_between(merge_df['day_date'], merge_df[f'{channel}_min'], merge_df[f'{channel}_max'], alpha=0.2,
                            color=color_palette[zz])
            ylim_up = np.max(ymean[channel]) * 1.01
            x_min_note = merge_df.loc[merge_df['day_date'] == min(merge_df['day_date'])][channel].iloc[0]
            x_max_note = merge_df.loc[merge_df['day_date'] == max(merge_df['day_date'])][channel].iloc[0]
            year_factor = max(int((max(merge_df['day_date']).year - min(merge_df['day_date']).year) / 8), 1)
            ax.annotate(f"{round(x_min_note, 2)}", xy=(min(merge_df['day_date']), x_min_note),
                        xytext=(min(merge_df['day_date']), x_min_note - int(x_min_note / 10)))
            ax.annotate(f"{round(x_max_note, 2)}", xy=(max(merge_df['day_date']), x_max_note), xytext=(
            max(merge_df['day_date']) - pd.DateOffset(years=year_factor), x_max_note - int(x_min_note / 15)))

            if firstPlot:
                lg = ax.legend(loc='upper left', bbox_to_anchor=(0.5, 1.4))
                firstPlot = False
            ax.set_ylabel(ylab)
            ax.set_ylim(0, ylim_up)
            ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=8))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
            ax.set_xlabel('Year')
            ax.set_title('$\it{Pf}$PR$_{2-10}$' + f': {fi}')

        fname = f'timeseries_daily_{channel}_{agegrp}_by_{ii}'
        fig.savefig(os.path.join(fdir, f'{fname}.png'), bbox_extra_artists=(lg,), bbox_inches='tight')
        plt.close()

def daily_eradication(fdir, df_all, channel, sweepvar='modelname', facet_var='ageGroup', agegrp = '0-100', pop_size = None):

    #reductions = [f'25%-10%', f'50%-10%', f'50%-25%']
    #df_all = df_all[df_all['cc_title'].isin(reductions)]
    df_all = df_all[df_all['cc_change'] < df_all['target_output_values']]
   

    if facet_var != 'ageGroup' and agegrp is not None:
        df = df_all[(df_all.ageGroup == agegrp)]
    if facet_var != 'cm_clinical':
        df = df_all[(df_all.cm_clinical == np.min(df_all.cm_clinical))]
    if facet_var != 'seasonality':
        if 'perennial' in df.seasonality.unique():
            selected_season = 'perennial'
        else:
            selected_season = 'seasonal'
        df = df_all[(df_all.seasonality == selected_season)] 
               
    if agegrp is None:
        df = df_all.groupby(['timestep', sweepvar, facet_var, 'seed'])[channel].agg(np.mean).reset_index()
    
    if 'modelname' not in [sweepvar, facet_var] and len(df['modelname'].unique()) > 1:
            raise ValueError('modelname needs to be specified.')

    edf = pd.DataFrame(columns=['modelname','cc_title','total_sims','sims_failed','elimination_ratio'])
    for m, model in enumerate(df[sweepvar].unique()):
        model_df = df[df[sweepvar] == model]
        for i, (facet, facet_df) in enumerate(model_df.groupby([facet_var])):
            failed_sims = 0
            total_sims = 0
            for si, (seeds, sdf) in enumerate(facet_df.groupby(['seed'])):
                if sdf.iloc[-1]['simulatedEIR'] == 0:
                    failed_sims += 1
                total_sims +=1
            elimination_ratio = failed_sims / total_sims
            edf.loc[len(edf)] = {'modelname': model, 'cc_title': facet, 'num_sims': total_sims,
                                'sims_failed': failed_sims, 'elimination_ratio': elimination_ratio} 
    edf['pop_size'] = pop_size
    edf.to_csv((os.path.join(fdir, 'elimination.csv')), index=False)

    


if __name__ == "__main__":
    args = parse_args()
    wdir = args.directory
    modelname = args.modelname   #  ['EMOD', 'malariasimulation', 'OpenMalaria']
    #out_dir = '/projects/b1139/emod-om/simulation_outputs/rer4177/test_sims_20240730/sims_dynamic_perennial_cc_step_15_11_55'
    #modelname = ['OpenMalaria']
    if isinstance(modelname, str):
        modelname = [modelname]

    exp = load_exp(wdir)

    df_cc, out_dir = get_output_df(wdir, modelname, custom_name='mmmpy_ccstep_daily')
    out_dir = os.path.join(out_dir, 'plots')
    os.makedirs(out_dir, exist_ok=True)

    sweepvar = 'modelname'
    facet_var = 'ageGroup'
    daily_channel_list = ['prevalence_2to10', 'prevalence', 'simulatedEIR', 'clinical_incidence', 'severe_incidence', 'n_total_mos_pop']
    facet_daily = 'cc_title'

    #daily_eradicaiton(wdir, df_cc, 'prevalence2to10', sweepvar=sweepvar, facet_var=facet_daily)
    #If you set agegrp to None, it will combine all ages, note, csv includes 0-5 and 0-100
    daily_timeseries(out_dir, df_cc, channel_list=daily_channel_list, sweepvar=sweepvar, facet_var=facet_daily, agegrp=None)
    daily_eradication(out_dir, df_cc, channel = 'simulatedEIR', sweepvar = sweepvar, facet_var=facet_daily, agegrp = None, pop_size=exp.pop_size)
    # daily_timeseries_by_seed(out_dir, df_cc, channel_list = daily_channel_list, sweepvar = sweepvar, facet_var = facet_daily, agegrp='0-100')
    # daily_vectors(out_dir, df_cc, channel='n_total_mos_pop', sweepvar=sweepvar, facet_var=facet_daily)
