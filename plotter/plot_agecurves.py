import argparse
import pickle
import os
import sys
import numpy as np
import pandas as pd
import matplotlib as mpl
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

mpl.rcParams['pdf.fonttype'] = 3
plt.rcParams.update({'font.size': 16})
plt.rcParams.update({'font.sans-serif': "Arial"})

parent_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
sys.path.append(parent_dir)
from plotter.plot_helper import *


# Plots over age - requires mmmpy_yr.csv
def age_curves(fdir, df, channel, sweepvar='modelname', facet_var='target_output_values', age_groups_aggregates=None, facet_name=None):

    """
    Plots age curves based on model results and saves the figure to the specified directory.

    Args:
        fdir (str): Directory where the plot will be saved.
        df (pandas.DataFrame): DataFrame that includes combined model results.
        channel (str): Variable representing the y-axis data to be plotted.
        sweepvar (str, optional): Variable to group the data and create multiple lines on the plot.
                                   Defaults to 'modelname'.
        facet_var (str, optional): Variable used to create subplots based on its unique values.
                                   Defaults to 'target_output_values'.
        age_groups_aggregates (list, optional): List of age group labels to use for aggregation.
                                                 If None, default age groups will be used.

    Raises:
        ValueError: If `facet_var` is set to 'ageGroup'.

    Returns:
        None: The function saves the generated plots to disk.

    Notes:
        - The function generates a multi-faceted plot with separate subplots for each unique value
          of the `facet_var` and lines representing the `sweepvar` variable.
        - Each subplot visualizes the age distribution of the specified `channel` variable, with
          filled areas representing the confidence interval.
    """

    if facet_name is None:
        facet_name = facet_var

    if facet_var == 'ageGroup':
        raise ValueError('Age curves designed to have age on the x-axis, ageGroup facets are not supported')

    if age_groups_aggregates is None:
        age_groups_aggregates = ['0-0.5', '0.5-1', '1-2', '2-5', '5-10', '10-15', '15-20', '20-100']

    figure_vars = [channel] + [sweepvar, facet_var]
    df, caption_txt = subset_dataframe_for_plot(df, figure_vars)

    firstPlot = True
    unique_facets = sorted_list(df[facet_var])
    unique_groups = sorted_list(df[sweepvar])
    color_palette = sns.color_palette('colorblind', max(len(df[sweepvar].unique()), 4))

    nx = max(1, round(len(unique_facets) / 2))
    ny = 2
    f = 1
    fig = plt.figure(figsize=(10 * nx, 10 * ny))
    for fi in unique_facets:
        fdf = df[df[facet_var] == fi]
        fdf = fdf[fdf[channel].notnull()]
        ax = fig.add_subplot(ny, nx, f)
        ax.set_title(f"{facet_var} = {fi}")
        if facet_var == 'modelname':
            ax.set_title(fi)
        if facet_var == 'target_output_values':
            ax.set_title(f"{get_label(facet_name)} = {fi}")

        f += 1
        max_ylim = []
        for i, (s, sdf) in enumerate(fdf.groupby([sweepvar])):
            s = s[0]
            color_key = color_selector(i, s)
            ylim_up = np.max(sdf[channel]) * 1.1
            if channel == 'prevalence' or channel == 'prevalence_2to10':
                ylim_up = min(ylim_up, 1)
            max_ylim.append(ylim_up)
            xmean, ymean = get_x_y(sdf, 'ageGroup', channel, channel)
            xmean = xmean['ageGroup']
            merge_df = pd.merge(left=xmean, right=ymean, on='ageGroup')
            merge_df['ageGroup'] = pd.Categorical(merge_df['ageGroup'], age_groups_aggregates)  # FIXME returns NA for 0-5 and 0-100, perhaps wanted
            merge_df = merge_df.dropna()
            merge_df.sort_values('ageGroup', inplace=True)
            ax.plot(merge_df['ageGroup'], merge_df[channel], '-', linewidth=0.8, label=f"{s}",
                    color=color_palette[color_key])
            ax.fill_between(merge_df['ageGroup'], merge_df[f'{channel}_min'], merge_df[f'{channel}_max'], alpha=0.1,
                            color=color_palette[color_key])
        if firstPlot:
            lg = ax.legend(loc='upper left', bbox_to_anchor=(0,1))
            firstPlot = False
        ax.set_ylim(0, max(max_ylim))
        ax.tick_params(axis='x', labelrotation=45)
        ax.set_xlabel('Age (years)')
        ax.set_ylabel(get_label(channel))

    fname = f'agecurves_{channel}_{sweepvar}_{facet_var}'
    fname = clean_fname(fname, sweepvar, unique_groups, facet_var, unique_facets)
    fig.savefig(os.path.join(fdir, f'{fname}.png'), bbox_extra_artists=(lg,), bbox_inches='tight')
    plt.close()


if __name__ == "__main__":
    args = parse_args()
    wdir = args.directory
    modelname = args.modelname
    if isinstance(modelname, str):
        modelname = [modelname]

    exp = load_exp(wdir)


    age_groups_aggregates_sub = [x for x in exp.age_groups_aggregates if x not in ([[0, 5], [0, 100]])]
    age_groups_aggregates_sub = ["{}-{}".format(sublist[0], sublist[1]) for sublist in age_groups_aggregates_sub]

    channel_list = ['clinical_incidence', 'severe_incidence', 'prevalence', 'simulatedEIR']
    sweepvar = 'modelname'
    facet_var = 'target_output_values'

    if len(exp.target_output_values) > 1 & len(exp.target_output_values) <= 3:
        facet_var = 'target_output_values'
    if facet_var == 'ageGroup' and len(exp.cm_clinical) > 1:
        facet_var = 'cm_clinical'
    if facet_var == 'ageGroup' and len(exp.seasonality) > 1:
        facet_var = 'seasonality'

    df, out_dir = get_output_df(wdir, modelname)
    out_dir = os.path.join(out_dir, 'plots')
    os.makedirs(out_dir, exist_ok=True)

    for channel in channel_list:
        print(f'#----- Plotting Age Curves for {channel}-----#')
        age_curves(out_dir, df, channel=channel, sweepvar=sweepvar, facet_var=facet_var,  age_groups_aggregates=age_groups_aggregates_sub)

    sweepvar =  'target_output_values'
    facet_var =  'modelname'
    for channel in channel_list:
        print(f'#----- Plotting Age Curves for {channel}-----#')
        age_curves(out_dir, df, channel=channel, sweepvar=sweepvar, facet_var=facet_var,  age_groups_aggregates=age_groups_aggregates_sub)
