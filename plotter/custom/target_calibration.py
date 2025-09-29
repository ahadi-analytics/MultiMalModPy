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
import manifest


def target_calibration_plot(
    fdir,
    df,
    sweepvar=["seasonality"],  # list of columns to combine for grouping
    channels=["clinical_incidence"],
    width_per_col=8,
    height_per_row=6,
    space=0.4,
    file_format="png",
):
    """
    Generate a single figure with subplots faceted by channels, lines grouped by combined sweepvar.

    Args:
        fdir (str): Directory to save plot.
        df (pd.DataFrame): DataFrame to plot.
        sweepvar (list of str): Columns combined to define groups.
        channels (list of str): Channels to plot as facets.
        width_per_col (float): Width per subplot.
        height_per_row (float): Height per subplot.
        space (float): Space between subplots.
        file_format (str): File format.

    Returns:
        None
    """

    # Combine sweepvar columns into one group string
    if isinstance(sweepvar, list) and len(sweepvar) > 1:
        combined_name = "_".join(sweepvar)
        df[combined_name] = df[sweepvar].astype(str).agg(" | ".join, axis=1)
        group_col = combined_name
    elif isinstance(sweepvar, list) and len(sweepvar) == 1:
        group_col = sweepvar[0]
    else:
        group_col = sweepvar

    unique_groups = sorted_list(df[group_col])
    num_colors = len(unique_groups)
    n_channels = len(channels)

    fig, axs = plt.subplots(
        1,
        n_channels,
        figsize=(width_per_col * n_channels, height_per_row),
        squeeze=False,
    )
    axs = axs.flatten()
    model = df["models"].unique()[0]
    fig.suptitle(model, fontsize=14, y=1.05)

    for i, channel in enumerate(channels):
        ax = axs[i]

        for mi, grp in enumerate(unique_groups):
            pdf = df[df[group_col] == grp]
            color = color_selector(mi, grp, sweepvar=group_col, n_colors=num_colors)

            if not pd.isnull(pdf["input_target"]).all():
                pdf["input_target_grp"] = pdf["input_target"]
                xmean, ymean = get_x_y(pdf, "input_target", "input_target_grp", channel)
                merge_df = pd.merge(left=xmean, right=ymean, on="input_target")
                merge_df.sort_values(by="input_target", inplace=True)

                ax.plot(
                    merge_df["input_target"], merge_df[channel], label=grp, color=color
                )
                ax.fill_between(
                    merge_df["input_target"],
                    merge_df[f"{channel}_min"],
                    merge_df[f"{channel}_max"],
                    alpha=0.1,
                    color=color,
                )

        y_lim = 1 if channel == "prevalence" else max(df[channel].dropna()) * 1.1
        ax.set_ylim(0, y_lim)
        ax.set_xlim(0, max(df["input_target"].dropna()) * 1.1)
        ax.set_ylabel(channel)
        ax.set_xlabel("input_target")
        ax.set_title(channel)

    # Single legend for all subplots
    handles, labels = axs[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper right", title=group_col)

    fig.tight_layout()
    fig.subplots_adjust(right=0.85, hspace=space)

    fname = f'{model}target_input_to_{"_".join(channels)}'
    fig.savefig(
        os.path.join(fdir, f"{fname}.{file_format}"),
        format=file_format,
        bbox_inches="tight",
    )
    plt.close()


if __name__ == "__main__":
    fpath = os.path.join(manifest.ROOT_DIR, "target_calibration")
    fname = "interpolation_data.csv"

    emod_df = pd.read_csv(os.path.join(fpath, "EMOD", fname))
    malariasimulation_df = pd.read_csv(os.path.join(fpath, "malariasimulation", fname))
    openmalaria_df = pd.read_csv(os.path.join(fpath, "OpenMalaria", fname))

    fdir = os.path.join(manifest.ROOT_DIR, "plotter", "custom", "generated_plots")
    os.makedirs(fdir, exist_ok=True)

    target_calibration_plot(
        fdir=fdir,
        df=emod_df,
        sweepvar=["seasonality", "cm_clinical"],
        channels=["prevalence_2to10", "clinical_incidence_U5"],
        file_format="png",
    )

    target_calibration_plot(
        fdir=fdir,
        df=malariasimulation_df,
        sweepvar=["seasonality", "cm_clinical"],
        channels=["prevalence_2to10", "clinical_incidence_U5"],
        file_format="png",
    )

    target_calibration_plot(
        fdir=fdir,
        df=openmalaria_df,
        sweepvar=["seasonality", "cm_clinical"],
        channels=["prevalence_2to10", "clinical_incidence_U5"],
        file_format="png",
    )
