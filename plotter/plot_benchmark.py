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

from plot_helper import *


# Plots prevalence 2 to 10 by output variable, requires benchmark.csv
def prevalence2to10_to_incidence(fdir, df, sweepvar='modelname', facet_var='seasonality', channel='clinical_incidence',
                                 agegrps=None):
    """
    Generates line plots for PfPR2to10 and either clinical or severe incidence per sweepvar as colors and modelname as panels.
    Parameters:
        fdir (str): Directory where the plot will be saved.
        modelname (str or list of str): Name of models for which result dataframes should be loaded.
        sweepvar (str, optional): Variable to group the data and create multiple panels on the plot. Default is 'modelname'.
        channel (str): Variable representing the y-axis data to be plotted.
    Returns:
        None (plots are saved to disk).
    """

    figure_vars = ['prevalence_2to10', channel] + [sweepvar, facet_var]
    df, caption_txt = subset_dataframe_for_plot(df, figure_vars, agegrps)

    unique_facets = df[facet_var].unique()
    nx = len(df['ageGroup'].unique())
    ny = 1
    f = 1
    firstPlot = True
    fig = plt.figure(figsize=(10 * nx, 10 * ny))

    unique_groups = df[sweepvar].unique()
    unique_groups = np.sort(unique_groups)
    num_colors = len(unique_groups)
    color_palette = sns.color_palette('colorblind', max(num_colors, 4))

    # for each age group, plot x = prevalence 2_to_10, y = incidences (or prevalence)
    for fi in unique_facets:
        fdf = df[df[facet_var] == fi]

        for agroup in fdf['ageGroup'].unique():
            ax = fig.add_subplot(ny, nx, f)
            ax.set_title(f'{fi}, {agroup}')
            f += 1
            adf = fdf[fdf.ageGroup == agroup]

            for mi, model in enumerate(unique_groups):
                pdf = adf[adf[sweepvar] == model]
                color_key = color_selector(mi, model)
                if not pd.isnull(pdf['prevalence_2to10']).all():
                    # plot mean, min and max of seeds
                    xmean, ymean = get_x_y(pdf, 'output_target', 'prevalence_2to10', channel)
                    merge_df = pd.merge(left=xmean, right=ymean, on='output_target')
                    if channel == 'simulatedEIR':
                        merge_df.sort_values(by='output_target', inplace=True)
                    else:
                        merge_df.sort_values(by='prevalence_2to10', inplace=True)
                    ax.plot(merge_df['prevalence_2to10'], merge_df[channel], label=model,
                            color=color_palette[color_key])
                    ax.fill_between(merge_df['prevalence_2to10'], merge_df[f'{channel}_min'],
                                    merge_df[f'{channel}_max'], alpha=0.1, color=color_palette[color_key])
            if channel == "prevalence":
                y_lim = 1
            else:
                y_lim = max(adf[channel]) * 1.1
            ax.set_ylim(0, y_lim)
            ax.set_xlim(0, 1)
            ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1])
            ax.title.set_text(f'{agroup}')
            ax.set_ylabel(get_ylab(channel))
            ax.set_xlabel('$\it{Pf}$PR$_{2-10}$ (%)')
            if firstPlot:
                lg = ax.legend(loc='upper left', bbox_to_anchor=(0.5, 1.2))
                firstPlot = False

    fname = f'pfpr2to10_to_{channel}'
    fig.savefig(os.path.join(fdir, f'{fname}.png'), bbox_extra_artists=(lg,), bbox_inches='tight')
    plt.close()


# Plots prevalence 2 to 10 by incidence, with subplots seperated by 3 age groups. These graphs were requested by Narimane to reflect 
# figure 1 in https://www.nature.com/articles/ncomms9170
def prevalence2to10_to_incidence_by_age_and_model(fdir, df, sweepvar='modelname', channel='clinical_incidence'):
    """
    Generates line plots for PfPR2to10 and either clinical or severe incidence as panels seperated by model (columns) and ages (rows).
    Parameters:
        fdir (str): Directory where the plot will be saved.
        modelname (str or list of str): Name of models for which result dataframes should be loaded.
        sweepvar (str, optional): Variable to group the data and create multiple panels on the plot. Default is 'modelname'.
        channel (str): Variable representing the y-axis data to be plotted.
    Returns:
        None (plots are saved to disk).
    """

    seasonality = list(df['seasonality'].unique())
    nx = 3
    ny = 3
    f = 1
    fig = plt.figure(figsize=(10 * nx, 10 * ny))

    unique_groups = df[sweepvar].unique()
    unique_groups = np.sort(unique_groups)
    num_colors = len(unique_groups)
    color_palette = sns.color_palette('colorblind', max(num_colors, 4))
    young_child = ['0-0.5', '0.5-1', '1-2', '2-5']
    older_child = ['5-10', '10-15']
    adult = ['15-20', '20-100']
    ages_list = [young_child, older_child, adult]
    mean_vars = [channel, 'prevalence_2to10']

    # for each age group, plot x = prevalence 2_to_10, y = incidences (or prevalence)
    for si, season in enumerate(seasonality):
        sdf = df[df.seasonality == season]
        for ages in ages_list:
            adf = sdf[sdf['ageGroup'].isin(ages)]
            for mi, model in enumerate(unique_groups):
                color_key = color_selector(mi, model)
                ax = fig.add_subplot(ny, nx, f)
                ax.set_title(f'{season} {model}')
                f += 1
                mdf = adf[adf.modelname == model]
                mdf = mdf.groupby(['seed', 'output_target'])[mean_vars].agg(np.mean).reset_index()
                if not pd.isnull(mdf['prevalence_2to10']).all():
                    # plot mean, min and max of seeds
                    xmean, ymean = get_x_y(mdf, 'output_target', 'prevalence_2to10', channel)
                    merge_df = pd.merge(left=xmean, right=ymean, on='output_target')
                    merge_df.sort_values(by='prevalence_2to10', inplace=True)
                    ax.plot(merge_df['prevalence_2to10'], merge_df[channel], label=model,
                            color=color_palette[color_key])
                    ax.fill_between(merge_df['prevalence_2to10'], merge_df[f'{channel}_min'],
                                    merge_df[f'{channel}_max'], alpha=0.1, color=color_palette[color_key])
                if channel == "prevalence":
                    y_lim = 1
                else:
                    y_lim = max(adf[channel]) * 1.01
                ax.set_ylim(0, y_lim)
                ax.set_xlim(0, 1)
                ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1])
                ax.title.set_text(f'{model}: {ages}')
                ax.set_ylabel(get_ylab(channel))
                ax.set_xlabel('$\it{Pf}$PR$_{2-10}$ (%)')
    fname = f'pfpr2to10_to_{channel}_by_age_by_model'
    fig.savefig(os.path.join(fdir, f'{fname}.png'), bbox_inches='tight')
    plt.close()


# Plots simulated eir vs output variable, requires benchmark.csv
def eir_to_outcome(fdir, df, sweepvar='cm_clinical', facet_var='seasonality', eir_val='simulatedEIR',
                   channel='prevalence_2to10', agegrp='0-5'):
    """
    Generates line plots for EIR (input or simulated) and a requested outcome variable per modelname as colors and sweepvar as panels.
    Parameters:
        fdir (str): Directory where the plot will be saved.
        df (pandas dataframe): Dataframe that includes combined model results.
        sweepvar (str, optional): Variable to group the data and create multiple panels on the plot. Default is 'cm_clinical'.
        eir_val (str, optional): The EIR (entomological inoculation rate) value to be used for plotting. Default is 'simulatedEIR'.
        channel (str, optional): the outcome variable to compare to eir
        agegrp (str, optional): Limits the resulting graphs to the selected age group. Default 0-5.
    Returns:
        None (plots are saved to disk).
    """

    figure_vars = [eir_val, channel] + [sweepvar, facet_var]
    df, caption_txt = subset_dataframe_for_plot(df, figure_vars, agegrp)
    color_palette = sns.color_palette('colorblind', max(len(df[sweepvar].unique()), 4))

    firstPlot = True
    unique_facets = df[facet_var].unique()
    nx = len(df[sweepvar].unique())
    ny = len(unique_facets)
    f = 1
    fig = plt.figure(figsize=(10 * nx, 10 * ny))

    for fi in unique_facets:
        ax = fig.add_subplot(ny, nx, f)
        ax.set_title(fi)
        f += 1
        fdf = df[(df[facet_var] == fi)]

        for i, (p, pdf) in enumerate(fdf.groupby([sweepvar])):
            color_key = color_selector(i, p)
            xmean, ymean = get_x_y(pdf, 'output_target', eir_val, channel)  # get values for x and y axes.
            merge_df = pd.merge(left=xmean, right=ymean, on='output_target')
            merge_df.sort_values(by=eir_val, inplace=True)
            ax.plot(merge_df[eir_val], merge_df[channel], '-', linewidth=0.8, label=f"{p}",
                    color=color_palette[color_key])
            ax.fill_between(merge_df[eir_val], merge_df[f'{channel}_min'], merge_df[f'{channel}_max'], alpha=0.1,
                            color=color_palette[color_key])
        if firstPlot:
            lg = ax.legend(loc='upper left', bbox_to_anchor=(0, 1))
            firstPlot = False
        ax.set_xlim(0.1, 1000)
        ax.set_xscale('symlog')
        ax.set_xlabel(f'{eir_val.replace("EIR", " annual EIR")}', fontsize=14)
        ax.set_ylabel(get_ylab(channel))

    fname = f'{eir_val}_{channel}_{agegrp}_by_{sweepvar}_{facet_var}'
    if channel == 'prevalene_2to10':
        fname = f'{eir_val}_{channel}_by_{sweepvar}_{facet_var}'
    fname = fname.replace('modelname', 'model')

    fig.savefig(os.path.join(fdir, f'{fname}.png'), bbox_extra_artists=(lg,), bbox_inches='tight')
    plt.close()


def input_to_simulated_eir(fdir, df, sweepvar='cm_clinical', facet_var='seasonality'):
    """
    Generates line plots input compared to simulated EIR.
    Parameters:
        fdir (str): Directory where the plot will be saved.
        df (pandas dataframe): Dataframe that includes combined model results.
        sweepvar (str, optional): Variable to group the data and create multiple lines on the plot. Default is 'cm_clinical'.
    Returns:
        None (plots are saved to disk).
    """
    xyvars = ['simulatedEIR', 'output_target']
    figure_vars = xyvars + [sweepvar, facet_var]
    df, caption_txt = subset_dataframe_for_plot(df, figure_vars)
    unique_facets = df[facet_var].unique()
    unique_groups = df[sweepvar].unique()
    unique_groups = np.sort(unique_groups)
    num_colors = len(unique_groups)
    color_palette = sns.color_palette('colorblind', max(num_colors, 4))
    firstPlot = True
    nx = 1
    ny = len(unique_facets)
    f = 1
    fig = plt.figure(figsize=(10 * nx, 6 * ny))
    for fi in unique_facets:
        fdf = df[df[facet_var] == fi]

        ax = fig.add_subplot(ny, nx, f)
        ax.set_title(fi)
        f += 1
        for i, (p, pdf) in enumerate(fdf.groupby([sweepvar])):
            # plot mean, min and max of seeds and age groups
            color_key = color_selector(i, p)
            if p == 'EMOD':
                model = 'em'
            elif p == 'OpenMalaria':
                model = 'om'
            elif p == 'MalSim':
                model = 'ms'
            else:
                print(f'Warning: Model not recognized: {p}')
            xmean, ymean = get_x_y(pdf, 'output_target', f'model_input_{model}', 'simulatedEIR')
            merge_df = pd.merge(left=xmean, right=ymean, on='output_target')
            merge_df.sort_values(by=f'model_input_{model}', inplace=True)
            ax.plot(merge_df[f'model_input_{model}'], merge_df['simulatedEIR'], '-', linewidth=0.8, label=f"{p}",
                    color=color_palette[color_key])
            ax.fill_between(merge_df[f'model_input_{model}'], merge_df['simulatedEIR_min'],
                            merge_df['simulatedEIR_max'], alpha=0.1, color=color_palette[color_key])
        if firstPlot:
            lg = ax.legend(loc='upper left', bbox_to_anchor=(0, 1))
            firstPlot = False
        ax.set_ylim(0.1, 10000)
        ax.set_xlim(0.1, 10000)
        ax.set_yscale('symlog')
        ax.set_xscale('symlog')

    plt.xlabel('Input EIR')
    plt.ylabel('Simulated annual EIR')

    # if ny == 2:
    #    fig.text(0.95, 0.25, seasonality[1], ha='center', va='center', rotation=-90, fontsize=14)
    fname = f'input_to_simulated_eir_by_{sweepvar}_{facet_var}'
    fname = fname.replace('modelname', 'model')
    fig.savefig(os.path.join(fdir, f'{fname}.png'), bbox_extra_artists=(lg,), bbox_inches='tight')
    plt.close()


# Calculates ANOVA scores for each output variable, requires Benchmark.csv
def anovas(fdir, df):
    """
    Calculates ANOVA scores for each output variable, seperated by age group and all ages.
    Parameters:
        fdir (str): Directory where the plot will be saved.
        df (pandas dataframe): Dataframe that includes combined model results.
    Returns:
        None (ANOVA values are saved to disk).
    """
    from scipy.stats import f_oneway
    comparisons = ['prevalence_2to10', 'prevalence', 'clinical_incidence', 'severe_incidence', 'simulatedEIR']
    emod = df[df['modelname'] == 'EMOD']
    malsim = df[df['modelname'] == 'MalSim']
    openmalaria = df[df['modelname'] == 'OpenMalaria']

    anova_df = pd.DataFrame(columns=['Age Group', 'Objective', 'F_value', 'p_value', 'null_hyp'])

    # As a whole
    for com in comparisons:
        performance_emod = emod[com]
        performance_malsim = malsim[com]
        performance_openmalaria = openmalaria[com]
        f_value, p_value = f_oneway(performance_emod, performance_malsim, performance_openmalaria)
        if p_value <= 0.05:
            null_hyp = True
        else:
            null_hyp = False
        new_row = {'Age Group': 'Across All Ages', 'Objective': com, 'F_value': f_value, 'p_value': p_value,
                   'null_hyp': null_hyp}
        anova_df = pd.concat([anova_df, pd.DataFrame([new_row])], ignore_index=True)

    # By Age Group
    for age in df['ageGroup'].unique():
        em = emod[emod['ageGroup'] == age]
        ms = malsim[malsim['ageGroup'] == age]
        om = openmalaria[openmalaria['ageGroup'] == age]
        for com in comparisons:
            performance_emod = em[com]
            performance_malsim = ms[com]
            performance_openmalaria = om[com]
            f_value, p_value = f_oneway(performance_emod, performance_malsim, performance_openmalaria)
            if p_value <= 0.05:
                null_hyp = True
            else:
                null_hyp = False
            new_row = {'Age Group': age, 'Objective': com, 'F_value': f_value, 'p_value': p_value, 'null_hyp': null_hyp}
            anova_df = pd.concat([anova_df, pd.DataFrame([new_row])], ignore_index=True)

    anova_df.to_csv(os.path.join(fdir, 'anovas.csv'), index=False)


# Calculates RMSE values for each output variable
def rmse(fdir, df):
    """
    Calculates RMSE scores for each output variable (comparing against each model individually), seperated by age group and all ages.
    Parameters:
        fdir (str): Directory where the plot will be saved.
        df (pandas dataframe): Dataframe that includes combined model results.
    Returns:
        None (RMSE scores are saved to disk).
    """
    from sklearn.metrics import mean_squared_error
    from math import sqrt

    rmse_vars = ['prevalence_2to10', 'prevalence', 'clinical_incidence', 'severe_incidence', 'simulatedEIR']

    rmse_df = pd.DataFrame(
        columns=['Age Group', 'Variable', 'EMOD_TO_OPENMALARIA', 'OPENMALARIA_TO_MALSIM', 'EMOD_TO_MALSIM'])

    for rmse_var in rmse_vars:
        group_data = df.groupby(['modelname'])[rmse_var].agg(['mean']).reset_index()
        emod_data = group_data[group_data['modelname'] == 'EMOD']
        malsim_data = group_data[group_data['modelname'] == 'MalSim']
        om_data = group_data[group_data['modelname'] == 'OpenMalaria']
        # RMSE Between EMOD and OM
        rmse_eo = sqrt(mean_squared_error(emod_data['mean'], om_data['mean']))
        # RMSE Between OM AND MALSIM
        rmse_om = sqrt(mean_squared_error(malsim_data['mean'], om_data['mean']))
        # RMSE Between EMOD and Malsim
        rmse_em = sqrt(mean_squared_error(emod_data['mean'], malsim_data['mean']))
        # RMSE Concat
        new_row = {'Age Group': 'Across All Ages', 'Variable': rmse_var, 'EMOD_TO_OPENMALARIA': rmse_eo,
                   'OPENMALARIA_TO_MALSIM': rmse_om, 'EMOD_TO_MALSIM': rmse_em}
        rmse_df = pd.concat([rmse_df, pd.DataFrame([new_row])], ignore_index=True)

    for age in df['ageGroup'].unique():
        adf = df[df['ageGroup'] == age]
        for rmse_var in rmse_vars:
            group_data = adf.groupby(['modelname'])[rmse_var].agg(['mean']).reset_index()
            emod_data = group_data[group_data['modelname'] == 'EMOD']
            malsim_data = group_data[group_data['modelname'] == 'MalSim']
            om_data = group_data[group_data['modelname'] == 'OpenMalaria']
            # RMSE Between EMOD and OM
            rmse_eo = sqrt(mean_squared_error(emod_data['mean'], om_data['mean']))
            # RMSE Between OM AND MALSIM
            rmse_om = sqrt(mean_squared_error(malsim_data['mean'], om_data['mean']))
            # RMSE Between EMOD and Malsim
            rmse_em = sqrt(mean_squared_error(emod_data['mean'], malsim_data['mean']))
            # RMSE DF
            new_row = {'Age Group': age, 'Variable': rmse_var, 'EMOD_TO_OPENMALARIA': rmse_eo,
                       'OPENMALARIA_TO_MALSIM': rmse_om, 'EMOD_TO_MALSIM': rmse_em}
            rmse_df = pd.concat([rmse_df, pd.DataFrame([new_row])], ignore_index=True)
    rmse_df.to_csv(os.path.join(fdir, 'rmse.csv'), index=False)


if __name__ == "__main__":
    args = parse_args()
    wdir = args.directory
    modelname = args.modelname
    if isinstance(modelname, str):
        modelname = [modelname]
    file = open(os.path.join(wdir, "exp.obj"), "rb")
    exp = pickle.load(file)

    df, out_dir = get_output_df(wdir, modelname)
    out_dir = os.path.join(out_dir, 'plots')
    os.makedirs(out_dir, exist_ok=True)

    quantitative = False
    if quantitative and len(modelname) == 3:
        print('#----- Calculating RMSE Values and ANOVAs -----#')
        rmse(out_dir, modelname)
        anovas(out_dir, modelname)

    if len(exp.output_target) >= 3:
        sweepvar = 'modelname'
        print('#----- Plotting input to simulated EIR -----#')
        input_to_simulated_eir(out_dir, df, sweepvar=sweepvar)

        channel_list = ['prevalence_2to10', 'prevalence', 'clinical_incidence', 'severe_incidence']
        for channel in channel_list:
            print(f'#----- Plotting simulated EIR to {channel} -----#')
            eir_to_outcome(out_dir, df, sweepvar=sweepvar, facet_var='seasonality', eir_val='simulatedEIR', channel=channel, agegrp='0-100')

        channel_list = ['clinical_incidence', 'severe_incidence', 'prevalence', 'simulatedEIR']
        for channel in channel_list:
            print(f'#----- Plotting prevalence_2_to_10 to {channel} -----#')
            prevalence2to10_to_incidence(out_dir, df, channel=channel)
            # prevalence2to10_to_incidence_by_age_and_model(out_dir,modelname,channel=channel) #This is new plotter, we don't have to make it everytime, but its available.
    else:
        print(f'Too few EIR values to be able to run relationship plots')
