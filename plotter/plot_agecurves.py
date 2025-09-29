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

mpl.rcParams["pdf.fonttype"] = 3
plt.rcParams.update({"font.size": 16})
plt.rcParams.update({"font.sans-serif": "Arial"})

parent_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
sys.path.append(parent_dir)
from plotter.plot_helper import *


# Plots over age - requires mmmpy_yr.csv
def age_curves(
    fdir,
    df,
    channel,
    sweepvar="models",
    facet_var="target_output_values",
    age_groups_aggregates=None,
    facet_name=None,
    exp=None,
    facet_layout=None,
    width_per_col=8,
    height_per_row=8,
    space=0.4,
    file_format="png",
):
    """
    Plots age curves based on model results and saves the figure to the specified directory.

    Args:
        fdir (str): Directory where the plot will be saved.
        df (pandas.DataFrame): DataFrame that includes combined model results.
        channel (str): Variable representing the y-axis data to be plotted.
        sweepvar (str, optional): Variable to group the data and create multiple lines on the plot.
                                   Defaults to 'models'.
        facet_var (str, optional): Variable used to create subplots based on its unique values.
                                   Defaults to 'target_output_values'.
        age_groups_aggregates (list, optional): List of age group labels to use for aggregation.
                                                If None, default age groups will be used.
        facet_name (str, optional): Friendly name for facet_var in plot titles. If None, uses facet_var.
        exp (object, optional): Optional experiment object used for legend labeling.
        facet_layout (str or None, optional): Layout of subplots. One of:
            - 'horizontal': all facets in a single row
            - 'vertical': all facets in a single column
            - None: automatic grid layout (default)
        width_per_col (int or float, optional): Width of each subplot column in inches. Default is 8.
        height_per_row (int or float, optional): Height of each subplot row in inches. Default is 8.
        space (float, optional): Space between subplots (both hspace and wspace). Default is 0.4.
        file_format (str, optional): File format for saved figure. One of: 'png', 'pdf', 'jpg'. Default is 'png'.

    Raises:
        ValueError: If `facet_var` is set to 'ageGroup'.

    Returns:
        None: The function saves the generated plot to disk in the specified format.
    """

    if facet_name is None:
        facet_name = facet_var

    if facet_var == "ageGroup":
        raise ValueError(
            "Age curves designed to have age on the x-axis, ageGroup facets are not supported"
        )

    if age_groups_aggregates is None:
        age_groups_aggregates = [
            "0-0.5",
            "0.5-1",
            "1-2",
            "2-5",
            "5-10",
            "10-15",
            "15-20",
            "20-100",
        ]

    figure_vars = [channel] + [sweepvar, facet_var]
    df, caption_txt = subset_dataframe_for_plot(df, figure_vars)

    firstPlot = True
    unique_facets = sorted_list(df[facet_var])
    unique_groups = sorted_list(df[sweepvar])

    # Determine facet layout
    if facet_layout == "horizontal":
        nx = len(unique_facets)
        ny = 1
    elif facet_layout == "vertical":
        nx = 1
        ny = len(unique_facets)
    else:
        nx = max(1, round(len(unique_facets) / 2))
        ny = 2

    f = 1

    fig = plt.figure(figsize=(width_per_col * nx, height_per_row * ny))
    for fi in unique_facets:
        fdf = df[df[facet_var] == fi]
        fdf = fdf[fdf[channel].notnull()]
        ax = fig.add_subplot(ny, nx, f)
        ax.set_title(f"{facet_var} = {fi}")
        if facet_var == "models":
            ax.set_title(fi)
        if facet_var == "target_output_values":
            ax.set_title(f"{get_label(facet_name)} = {fi}")

        f += 1
        max_ylim = []
        for mi, grp in enumerate(unique_groups):
            sdf = fdf[fdf[sweepvar] == grp]
            color = color_selector(
                mi, grp, sweepvar=sweepvar, n_colors=len(unique_groups)
            )
            ylim_up = np.max(sdf[channel]) * 1.1
            if channel == "prevalence" or channel == "prevalence_2to10":
                ylim_up = min(ylim_up, 1)
            max_ylim.append(ylim_up)
            xmean, ymean = get_x_y(sdf, "ageGroup", channel, channel)
            xmean = xmean["ageGroup"]
            merge_df = pd.merge(left=xmean, right=ymean, on="ageGroup")
            merge_df["ageGroup"] = pd.Categorical(
                merge_df["ageGroup"], age_groups_aggregates
            )
            merge_df = merge_df.dropna()
            merge_df.sort_values("ageGroup", inplace=True)
            ax.plot(
                merge_df["ageGroup"],
                merge_df[channel],
                "-",
                linewidth=1,
                label=f"{mi}",
                color=color,
            )
            ax.fill_between(
                merge_df["ageGroup"],
                merge_df[f"{channel}_min"],
                merge_df[f"{channel}_max"],
                alpha=0.1,
                color=color,
            )
        if firstPlot:
            lg_title = get_legend_title(sweepvar, exp)
            lg = ax.legend(title=lg_title, loc="upper left", bbox_to_anchor=(0, 1))
            firstPlot = False
        ax.set_ylim(0, max(max_ylim))
        ax.tick_params(axis="x", labelrotation=45)
        ax.set_xlabel("Age (years)")
        ax.set_ylabel(get_label(channel))

    fname = f"agecurves_{channel}_{sweepvar}_{facet_var}"
    fname = clean_fname(fname, sweepvar, unique_groups, facet_var, unique_facets)
    fig.tight_layout()
    fig.subplots_adjust(hspace=space, wspace=space)
    fig.savefig(
        os.path.join(fdir, f"{fname}.{file_format}"),
        format=file_format,
        bbox_extra_artists=(lg,),
        bbox_inches="tight",
    )
    plt.close()


if __name__ == "__main__":
    args = parse_args()
    wdir = args.directory
    models = args.models
    if isinstance(models, str):
        models = [models]

    exp = load_exp(wdir)

    age_groups_aggregates_sub = [
        x for x in exp.age_groups_aggregates if x not in ([[0, 5], [0, 100]])
    ]
    age_groups_aggregates_sub = [
        "{}-{}".format(sublist[0], sublist[1]) for sublist in age_groups_aggregates_sub
    ]

    channel_list = ["clinical_incidence", "severe_incidence", "prevalence", "eir"]
    sweepvar = "models"
    facet_var = "target_output_values"

    if len(exp.target_output_values) > 1 & len(exp.target_output_values) <= 3:
        facet_var = "target_output_values"
    if facet_var == "ageGroup" and len(exp.cm_clinical) > 1:
        facet_var = "cm_clinical"
    if facet_var == "ageGroup" and len(exp.seasonality) > 1:
        facet_var = "seasonality"

    df, out_dir = get_output_df(wdir, models)
    out_dir = os.path.join(out_dir, "plots")
    if len(models) == 1 and len(exp.models) > 1:
        out_dir = os.path.join(out_dir, models[0])
    os.makedirs(out_dir, exist_ok=True)

    for channel in channel_list:
        print(f"#----- Plotting Age Curves for {channel}-----#")
        age_curves(
            out_dir,
            df,
            channel=channel,
            sweepvar=sweepvar,
            facet_var=facet_var,
            age_groups_aggregates=age_groups_aggregates_sub,
            exp=exp,
        )

    sweepvar = "target_output_values"
    facet_var = "models"
    for channel in channel_list:
        print(f"#----- Plotting Age Curves for {channel}-----#")
        age_curves(
            out_dir,
            df,
            channel=channel,
            sweepvar=sweepvar,
            facet_var=facet_var,
            age_groups_aggregates=age_groups_aggregates_sub,
            exp=exp,
        )
