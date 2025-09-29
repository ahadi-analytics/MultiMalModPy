import argparse
import pickle
import os
import sys
import numpy as np
import pandas as pd
import matplotlib as mpl
import seaborn as sns
import matplotlib.pyplot as plt

mpl.rcParams["pdf.fonttype"] = 3
plt.rcParams.update({"font.size": 16})
plt.rcParams.update({"font.sans-serif": "Arial"})

parent_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
sys.path.append(parent_dir)
from plotter.plot_helper import *


# Plots prevalence 2 to 10 by output variable, requires mmmpy_timeavrg.csv
def prevalence2to10_to_outcome(
    fdir,
    df,
    sweepvar="models",
    facet_var="ageGroup",
    channel="clinical_incidence",
    agegrps=None,
    exp=None,
    facet_layout=None,
    width_per_col=8,
    height_per_row=6,
    space=0.4,
    file_format="png",
):
    """
    Generate line plots for PfPR2to10 and either clinical or severe incidence,
    grouped by the specified sweep variable and faceted by another variable.

    This function creates a series of line plots where the x-axis represents
    the prevalence of PfPR2to10, and the y-axis represents either clinical or
    severe incidence. Each line corresponds to a model, and the plots can be
    faceted by a specified variable (e.g., seasonality).

    Args:
        fdir (str): Directory where the generated plot will be saved.
        df (pd.DataFrame): DataFrame containing the model results for plotting.
        sweepvar (str, optional): Variable to group the data and create multiple panels.
            Default is 'models'.
        facet_var (str, optional): Variable used to create subplots based on its unique
            values. Default is 'ageGroup'.
        channel (str): Variable representing the y-axis data to be plotted (e.g.,
            'clinical_incidence').
        agegrps (list of str, optional): Specific age groups to filter the DataFrame
            before plotting. Defaults to None, which means all age groups will be used.
        exp (object, optional): Experiment object used for labeling.
        facet_layout (str or None, optional): 'horizontal', 'vertical', or None for default layout.
        width_per_col (int or float, optional): Width of each subplot column in inches. Default is 8.
        height_per_row (int or float, optional): Height of each subplot row in inches. Default is 6.
        space (float, optional): Space between subplots (both hspace and wspace). Default is 0.4.
        file_format (str, optional): File format for saved figure. One of: 'png', 'pdf', 'jpg'. Default is 'png'.

    Returns:
        None: The function saves the generated plots to disk.

    Raises:
        ValueError: If an error occurs while filtering the DataFrame or during plotting.
    """

    figure_vars = ["prevalence_2to10", channel] + [sweepvar, facet_var]
    df, caption_txt = subset_dataframe_for_plot(df, figure_vars, agegrps)

    unique_facets = sorted_list(df[facet_var])
    unique_groups = sorted_list(df[sweepvar])

    # Layout logic
    if facet_layout == "horizontal":
        nx = len(unique_facets)
        ny = 1
    elif facet_layout == "vertical":
        nx = 1
        ny = len(unique_facets)
    else:
        nx = max(1, round(len(unique_facets) / 2))
        ny = (len(unique_facets) + nx - 1) // nx

    f = 1
    firstPlot = True
    fig = plt.figure(figsize=(width_per_col * nx, height_per_row * ny))

    # for each age group, plot x = prevalence 2_to_10, y = incidences (or prevalence)
    for fi in unique_facets:
        ax = fig.add_subplot(ny, nx, f)
        if facet_var == "ageGroup":
            ax.set_title(f"Age group: {fi}")
        else:
            ax.set_title(fi)
        f += 1
        adf = df[df[facet_var] == fi]

        for mi, grp in enumerate(unique_groups):
            pdf = adf[adf[sweepvar] == grp]
            color = color_selector(
                mi, grp, sweepvar=sweepvar, n_colors=len(unique_groups)
            )
            if not pd.isnull(pdf["prevalence_2to10"]).all():
                xmean, ymean = get_x_y(
                    pdf, "target_output_values", "prevalence_2to10", channel
                )
                merge_df = pd.merge(left=xmean, right=ymean, on="target_output_values")
                if channel == "eir":
                    merge_df.sort_values(by="target_output_values", inplace=True)
                else:
                    merge_df.sort_values(by="prevalence_2to10", inplace=True)
                ax.plot(
                    merge_df["prevalence_2to10"],
                    merge_df[channel],
                    label=grp,
                    color=color,
                )
                ax.fill_between(
                    merge_df["prevalence_2to10"],
                    merge_df[f"{channel}_min"],
                    merge_df[f"{channel}_max"],
                    alpha=0.1,
                    color=color,
                )
        if channel == "prevalence":
            y_lim = 1
        else:
            y_lim = max(adf[channel]) * 1.1
        ax.set_ylim(0, y_lim)
        ax.set_xlim(0, 1)
        ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1])
        ax.set_ylabel(get_label(channel))
        ax.set_xlabel("$\it{Pf}$PR$_{2-10}$ (%)")
        if firstPlot:
            lg_title = get_legend_title(sweepvar, exp)
            lg = ax.legend(loc="upper left", bbox_to_anchor=(0.5, 1.2), title=lg_title)
            firstPlot = False

    fname = f"pfpr2to10_to_{channel}_{sweepvar}_{facet_var}"
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


# Plots prevalence 2 to 10 by incidence, with subplots seperated by 3 age groups.
def prevalence2to10_to_outcome_by_age_and_model(
    fdir, df, channel="clinical_incidence", season=None
):
    """
    Generate grid plots of PfPR2to10 prevalence vs. clinical or severe incidence by age and model.

    This function creates a grid of line plots where:
      - The x-axis represents the prevalence of PfPR2to10.
      - The y-axis represents either clinical or severe incidence (as specified by the `channel` argument).
      - Rows correspond to different age groups.
      - Columns correspond to different models.

    The function aggregates data for each model and age group, computes mean and confidence intervals
    (min-max range), and plots these statistics with confidence bands.

    Args:
        fdir (str): Path to the directory where the resulting plot will be saved.
        df (pd.DataFrame): DataFrame containing the input data. Must include columns for model name,
            age group, prevalence, and incidence metrics.
        channel (str): The y-axis variable to plot (e.g., 'clinical_incidence', 'severe_incidence').
            Defaults to 'clinical_incidence'.
        season (str, optional): Seasonality condition to filter the data. If None, the first unique
            seasonality value in the dataset will be used. Defaults to None.

    Returns:
        None: The function generates and saves a plot as a PNG file in the specified directory.

    Notes:
        - Age groups are categorized into infants and young children (0-5 years), older children
          (5-15 years), and adults (>15 years).
        - Models are distinguished using unique colors.
        - The function requires helper functions for selecting colors (`color_selector`) and for
          data aggregation (`get_x_y`).
    """

    unique_groups = sorted_list(df["models"])

    # Define the age categories
    age_categories = {
        "young_child": {"min": 0, "max": 5},
        "older_child": {"min": 5, "max": 15},
        "adult": {"min": 15, "max": float("inf")},
    }
    ages_dict = {"young_child": [], "older_child": [], "adult": []}
    ages_labels = [
        "Infants and young\nchildren(0-5 yrs)",
        "Older children\n(5-15 yrs)",
        "Adults\n(>15 yrs)",
    ]

    # Assign each age range to the appropriate category
    age_ranges = [
        [start, end]
        for start, end in (item.split("-") for item in list(df["ageGroup"].unique()))
    ]
    for age_range in age_ranges:
        category = assign_age_group(age_range, age_categories)
        if category:
            age_range_str = f"{age_range[0]}-{age_range[1]}"
            ages_dict[category].append(age_range_str)
        else:
            print(f"Age range {age_range} does not fit any category.")

    mean_vars = [channel, "prevalence_2to10"]

    nx = max(1, len(models))
    ny = max(1, len(ages_dict))
    f = 1
    fig = plt.figure(figsize=(10 * nx, 6 * ny))

    # for each age group, plot x = prevalence 2_to_10, y = incidences (or prevalence)
    if season is None:
        season = df.seasonality.unique()[0]
    sdf = df[df.seasonality == season]

    for a, ages in enumerate(ages_dict.values()):
        adf = sdf[sdf["ageGroup"].isin(ages)]

        for mi, grp in enumerate(unique_groups):
            color = color_selector(
                mi, grp, sweepvar=sweepvar, n_colors=len(unique_groups)
            )
            ax = fig.add_subplot(ny, nx, f)
            ax.title.set_text(f"{grp}")

            f += 1
            mdf = adf[adf["models"] == grp]
            # mdf = mdf.groupby(['seed', 'target_output_values'])[mean_vars].agg(np.mean).reset_index()
            # Population weighted mean for each target_output_values (relevant for incidence)
            mdf = (
                mdf.groupby(["seed", "target_output_values"])[mean_vars + ["nHost"]]
                .apply(
                    lambda x: pd.Series(
                        {
                            col: np.average(x[col], weights=x["nHost"])
                            for col in mean_vars
                        }
                    )
                )
                .reset_index()
            )

            if not pd.isnull(mdf["prevalence_2to10"]).all():
                # plot mean, min and max of seeds
                xmean, ymean = get_x_y(
                    mdf, "target_output_values", "prevalence_2to10", channel
                )
                merge_df = pd.merge(left=xmean, right=ymean, on="target_output_values")
                merge_df.sort_values(by="prevalence_2to10", inplace=True)
                ax.plot(
                    merge_df["prevalence_2to10"],
                    merge_df[channel],
                    label=grp,
                    color=color,
                )
                ax.fill_between(
                    merge_df["prevalence_2to10"],
                    merge_df[f"{channel}_min"],
                    merge_df[f"{channel}_max"],
                    alpha=0.1,
                    color=color,
                )
            if channel == "prevalence":
                y_lim = 1
            else:
                y_lim = max(adf[channel]) * 1.01
            ax.set_ylim(0, y_lim)
            ax.set_xlim(0, 1)
            ax.set_xticks([0, 0.20, 0.40, 0.60, 0.80, 1])
            ax.set_ylabel(f"{ages_labels[a]}\n,{get_label(channel)}")
            ax.set_xlabel("$\it{Pf}$PR$_{2-10}$")

    fname = f"pfpr2to10_to_{channel}_age_model_{season}"
    fig.savefig(os.path.join(fdir, f"{fname}.png"), bbox_inches="tight")
    plt.close()


# Plots simulated eir vs output variable, requires mmmpy_timeavrg.csv
def eir_to_outcome(
    fdir,
    df,
    sweepvar="models",
    facet_var="seasonality",
    eir_val="eir",
    channel="prevalence_2to10",
    agegrps=["0-5"],
    exp=None,
    facet_layout=None,
    width_per_col=8,
    height_per_row=6,
    space=0.4,
    file_format="png",
):
    """
    Generate line plots for EIR (Entomological Inoculation Rate) and a requested
    outcome variable, with models represented as colors and sweep variables as panels.

    This function creates line plots where the x-axis represents the EIR and the
    y-axis represents an outcome variable, with different models indicated by color
    and organized into panels based on specified facets.

    Args:
        fdir (str): Directory where the generated plot will be saved.
        df (pd.DataFrame): DataFrame that includes combined model results.
        sweepvar (str, optional): Variable to group the data and create multiple
            panels on the plot. Default is 'models'.
        facet_var (str, optional): Variable used to facet subplots. Default is 'seasonality'.
        eir_val (str, optional): The EIR (Entomological Inoculation Rate) value to
            be used for plotting. Default is 'eir'.
        channel (str, optional): The outcome variable to compare to EIR. Default is
            'prevalence_2to10'.
        agegrps (list of str, optional): Limits the resulting graphs to the selected age group(s).
            Default is ['0-5'].
        exp (object, optional): Experiment object for legend labeling.
        facet_layout (str or None, optional): 'horizontal', 'vertical', or None for default layout.
        width_per_col (int or float, optional): Width of each subplot column in inches. Default is 8.
        height_per_row (int or float, optional): Height of each subplot row in inches. Default is 6.
        space (float, optional): Space between subplots (hspace and wspace). Default is 0.4.
        file_format (str, optional): File format for saved figure. One of: 'png', 'pdf', 'jpg'. Default is 'png'.

    Returns:
        None: The function saves the generated plots to disk.
    """

    figure_vars = [eir_val, channel] + [sweepvar, facet_var]
    df, caption_txt = subset_dataframe_for_plot(df, figure_vars, agegrps)
    firstPlot = True
    unique_facets = sorted_list(df[facet_var])
    unique_groups = sorted_list(df[sweepvar])

    # Layout logic
    if facet_layout == "horizontal":
        nx = len(unique_facets)
        ny = 1
    elif facet_layout == "vertical":
        nx = 1
        ny = len(unique_facets)
    else:
        nx = max(1, round(len(unique_facets) / 2))
        ny = (len(unique_facets) + nx - 1) // nx

    f = 1
    fig = plt.figure(figsize=(width_per_col * nx, height_per_row * ny))

    for fi in unique_facets:
        ax = fig.add_subplot(ny, nx, f)
        ax.set_title(fi)
        if len(unique_facets) == 1:
            ax.set_title("")

        f += 1
        fdf = df[(df[facet_var] == fi)]

        for i, (s, sdf) in enumerate(fdf.groupby([sweepvar])):
            color = color_selector(i, s, sweepvar=sweepvar, n_colors=len(unique_groups))
            xmean, ymean = get_x_y(sdf, "target_output_values", eir_val, channel)
            merge_df = pd.merge(left=xmean, right=ymean, on="target_output_values")
            merge_df.sort_values(by=eir_val, inplace=True)
            ax.plot(
                merge_df[eir_val],
                merge_df[channel],
                "-",
                linewidth=0.8,
                label=f"{s}",
                color=color,
            )
            ax.fill_between(
                merge_df[eir_val],
                merge_df[f"{channel}_min"],
                merge_df[f"{channel}_max"],
                alpha=0.1,
                color=color,
            )

        if channel == "prevalence" or channel == "prevalence_2to10":
            y_lim = 1
        else:
            y_lim = max(sdf[channel]) * 1.1
        ax.set_ylim(0, y_lim)
        ax.set_xlim(0.1, 1000)
        ax.set_xscale("symlog")
        ax.set_xlabel(
            f'{eir_val.replace("eir", " Simulated EIR (annual)")}', fontsize=14
        )
        ax.set_ylabel(get_label(channel))

        if firstPlot:
            lg_title = get_legend_title(sweepvar, exp)
            lg = ax.legend(loc="upper left", bbox_to_anchor=(0, 1), title=lg_title)
            firstPlot = False

    fname = f"{eir_val}_{channel}_{agegrps[0]}_{sweepvar}_{facet_var}"
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


def input_to_simulated_eir(
    fdir,
    df,
    sweepvar="models",
    facet_var="seasonality",
    exp=None,
    facet_layout=None,
    width_per_col=8,
    height_per_row=6,
    space=0.4,
    file_format="png",
):
    """
    Generate line plots comparing input EIR to simulated EIR.

    This function creates line plots where the x-axis represents the input EIR values
    and the y-axis represents the simulated annual EIR. Different models are represented
    by different lines on the plot, and the plots are organized into panels based on
    specified facets.

    Args:
        fdir (str): Directory where the generated plot will be saved.
        df (pd.DataFrame): DataFrame that includes combined model results.
        sweepvar (str, optional): Variable to group the data and create multiple lines
            on the plot. Default is 'models'.
        facet_var (str, optional): Variable to create multiple panels on the plot.
            Default is 'seasonality'.
        exp (object, optional): Experiment object used for legend labeling.
        facet_layout (str or None, optional): 'horizontal', 'vertical', or None for automatic layout.
        width_per_col (int or float, optional): Width of each subplot column in inches. Default is 8.
        height_per_row (int or float, optional): Height of each subplot row in inches. Default is 6.
        space (float, optional): Space between subplots (hspace and wspace). Default is 0.4.
        file_format (str, optional): File format to save the figure. Default is 'png'.

    Returns:
        None: The function saves the generated plots to disk.
    """

    if sweepvar != "models" and facet_var != "models":
        print("Either sweepvar or facet_var should be models")
        return

    xyvars = ["eir", "target_output_values"]
    figure_vars = xyvars + [sweepvar, facet_var]
    df, caption_txt = subset_dataframe_for_plot(df, figure_vars)
    unique_facets = sorted_list(df[facet_var])
    unique_groups = sorted_list(df[sweepvar])
    firstPlot = True

    # Layout logic
    if facet_layout == "horizontal":
        nx = len(unique_facets)
        ny = 1
    elif facet_layout == "vertical":
        nx = 1
        ny = len(unique_facets)
    else:
        nx = max(1, round(len(unique_facets) / 2))
        ny = (len(unique_facets) + nx - 1) // nx

    f = 1
    fig = plt.figure(figsize=(width_per_col * nx, height_per_row * ny))

    for fi in unique_facets:
        fdf = df[df[facet_var] == fi]
        ax = fig.add_subplot(ny, nx, f)
        ax.set_title(fi)
        f += 1

        for i, (s, sdf) in enumerate(fdf.groupby([sweepvar])):
            color = color_selector(i, s, sweepvar=sweepvar, n_colors=len(unique_groups))
            if sweepvar == "models":
                xchannel = f"transmission_intensity_{s}"
            elif facet_var == "models":
                xchannel = f"transmission_intensity_{fi}"
            else:
                if len(sorted_list(df["models"])) == 1:
                    xchannel = f"transmission_intensity_{sorted_list(df['models'])[0]}"
                else:
                    raise ValueError("Either sweepvar or facet_var need to be models")

            xmean, ymean = get_x_y(sdf, "target_output_values", xchannel, "eir")
            merge_df = pd.merge(left=xmean, right=ymean, on="target_output_values")
            merge_df.sort_values(by=xchannel, inplace=True)
            ax.plot(
                merge_df[xchannel],
                merge_df["eir"],
                "-",
                linewidth=0.8,
                label=f"{s}",
                color=color,
            )
            ax.fill_between(
                merge_df[xchannel],
                merge_df["eir_min"],
                merge_df["eir_max"],
                alpha=0.1,
                color=color,
            )

        if firstPlot:
            lg_title = get_legend_title(sweepvar, exp)
            lg = ax.legend(loc="upper left", bbox_to_anchor=(0, 1), title=lg_title)
            firstPlot = False

        ax.set_ylim(0.1, 10000)
        ax.set_xlim(0.1, 10000)
        ax.set_yscale("symlog")
        ax.set_xscale("symlog")

    plt.xlabel("Input EIR")
    plt.ylabel("Simulated EIR (annual)")

    fname = f"input_to_simulated_eir_{sweepvar}_{facet_var}"
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
    df, out_dir = get_output_df(wdir, models)
    out_dir = os.path.join(out_dir, "plots")
    if len(models) == 1 and len(exp.models) > 1:
        out_dir = os.path.join(out_dir, models[0])
    os.makedirs(out_dir, exist_ok=True)

    if len(exp.target_output_values) >= 3:
        sweepvar = "models"
        print("#----- Plotting input to simulated EIR -----#")
        input_to_simulated_eir(out_dir, df, sweepvar=sweepvar)
        # input_to_simulated_eir(out_dir, df, sweepvar='cm_clinical', facet_var='models') # for paper 1

        channel_list = [
            "prevalence_2to10",
            "prevalence",
            "clinical_incidence",
            "severe_incidence",
        ]
        for channel in channel_list:
            print(f"#----- Plotting simulated EIR to {channel} -----#")
            eir_to_outcome(
                out_dir,
                df,
                sweepvar=sweepvar,
                facet_var="seasonality",
                eir_val="eir",
                channel=channel,
                agegrps=["0-100"],
            )

        channel_list = ["clinical_incidence", "severe_incidence", "prevalence", "eir"]
        for channel in channel_list:
            print(f"#----- Plotting prevalence_2_to_10 to {channel} -----#")
            agegrps = ["0-5", "0-100"]
            prevalence2to10_to_outcome(
                out_dir,
                df,
                channel=channel,
                sweepvar="models",
                facet_var="ageGroup",
                agegrps=agegrps,
            )

            # This figure reflects figure 1 in https://www.nature.com/articles/ncomms9170
            prevalence2to10_to_outcome_by_age_and_model(out_dir, df, channel=channel)
    else:
        print(f"Too few EIR values to be able to run relationship plots")
