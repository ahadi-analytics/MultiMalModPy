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


def all_age_sample_plot(
    wdir, df, model, timestep_var, sweep_variables, sample_channels
):
    """
    Generate a sample plot for all age data.
    This function aggregates data based on the provided sweep variables and generates a set of plots for specified channels.
    Each plot shows the mean of the channels over time (based on the provided timestep variable). The plots are saved as a PNG file.

    Args:
        wdir (str): Working directory where the 'All_Age_Outputs.csv' file is located, and where the plots will be saved.
        df (DataFrame): The input DataFrame containing the data for plotting, including columns for the sweep variables, timestep, and channels.
        model (str): The model name used in the file name of the saved plot.
        timestep_var (str): The name of the column that represents the timestep (or time variable).
        sweep_variables (list): List of columns to group the data by for plotting (e.g., different simulation conditions).
        sample_channels (list): List of column names representing the channels to be plotted (e.g., prevalence, incidence, etc.).

    Returns:
        None

    Saves:
        sampleplot_all_age_{model}.png: A PNG file containing the generated plots.
    """

    # Take mean across seeds
    sample_channels = [x for x in sample_channels if x in df.columns]

    # Round numeric sweep variables shown in legend
    for sweep_var in sweep_variables:
        if np.issubdtype(df[sweep_var].dtype, np.number):
            df[sweep_var] = df[sweep_var].round(4)

    n_channels = len(sample_channels)
    n_cols = 3
    n_rows = -(-n_channels // n_cols)  # Ceiling division for rows
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, 4 * n_rows))
    axes = axes.flatten()  # Flatten to iterate easily
    fig.subplots_adjust(
        hspace=0.4, wspace=0.3, left=0.05, right=0.95, bottom=0.1, top=0.9
    )

    # Plot each channel
    for ch, channel in enumerate(sample_channels):
        if channel in df.columns:
            ax = axes[ch]
            for i, (p, pdf) in enumerate(df.groupby(sweep_variables)):
                pdf_aggr = (
                    pdf.groupby([timestep_var] + sweep_variables)[sample_channels]
                    .mean()
                    .reset_index()
                )
                label = (
                    ", ".join([f"{var}: {val}" for var, val in zip(sweep_variables, p)])
                    if isinstance(p, tuple)
                    else f"{sweep_variables[0]}: {p}"
                )

                # Set color from the default color cycle (using 'C0', 'C1', 'C2' etc.)
                color = f"C{i % 10}"  # To handle more than 10 colors, cycling through 'C0', 'C1', ...
                for _, seed in enumerate(pdf["seed"].unique()):
                    seed_data = pdf[pdf["seed"] == seed]
                    ax.plot(
                        seed_data[timestep_var],
                        seed_data[channel],
                        "-",
                        linewidth=0.5,
                        alpha=0.3,
                        color=color,
                    )
                ax.plot(
                    pdf_aggr[timestep_var],
                    pdf_aggr[channel],
                    "-",
                    linewidth=0.75,
                    label=label,
                    color=color,
                )

            ax.set_title(channel, fontsize=10)
            ax.set_ylabel(channel)

            if ch == len(sample_channels) - 1:
                lg = ax.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1, 1))

    # Remove unused subplots
    for ax in axes[n_channels:]:
        fig.delaxes(ax)

    # Add overall labels
    fig.text(0.5, 0.02, f"Time [{timestep_var}]", ha="center", va="center", fontsize=12)
    fig.suptitle("All-Age Sample Plot", fontsize=16)

    # Save the plot
    fname = f"sampleplot_all_age_{model}.png"
    fig.savefig(
        os.path.join(wdir, "plots", fname),
        bbox_extra_artists=(lg,),
        bbox_inches="tight",
    )


if __name__ == "__main__":
    args = parse_args()
    wdir = args.directory
    models = args.models
    if isinstance(models, str):
        models = [models]

    exp = load_exp(wdir)
    exp_tags = [x.replace("case_management", "cm_clinical") for x in exp.sweep_list]

    if "EMOD" in models:
        sample_channels = [
            "Statistical Population",
            "Births",
            "Disease Deaths",
            "New Infections",
            "Newly Symptomatic",
            "New Clinical Cases",
            "New Severe Cases",
            "Fever Prevalence",
            "True Prevalence",
            "PCR Gametocyte Prevalence",
            "PCR Parasite Prevalence",
            "Blood Smear Parasite Prevalence",
            "PfHRP2 Prevalence",
            "Infectious Vectors",
            "EIR",
        ]
        df = pd.read_csv(os.path.join(wdir, "EMOD", "All_Age_Outputs.csv"))
        df["date"] = pd.to_datetime(df["date"])
        df["simday"] = (df["date"] - df["date"].min()).dt.days
        all_age_sample_plot(
            wdir,
            df,
            "EMOD",
            timestep_var="simday",
            sweep_variables=exp_tags,
            sample_channels=sample_channels,
        )

    if "OpenMalaria" in models:
        sample_channels = [
            "nHost",
            "nInfect",
            "nPatent",
            "totalInfs",
            "totalPatentInf",
            "nTreatments",
            "nUncomp",
            "nSevere",
            "nSeq",
            "nIndDeaths",
            "expectedSevere" "nDirDeaths",
            "inputEIR",
            "eir",
            "expectedDirectDeaths",
        ]
        df = pd.read_csv(os.path.join(wdir, "OpenMalaria", "All_Age_Outputs.csv"))
        all_age_sample_plot(
            wdir,
            df,
            "OpenMalaria",
            timestep_var="survey",
            sweep_variables=exp_tags,
            sample_channels=sample_channels,
        )

    if "malariasimulation" in models:
        sample_channels = [
            "nPopulation",
            "n",
            "n_inc",
            "n_inc_clinical",
            "n_inc_severe",
            "clinical_incidence",
            "prevalence_2to10",
            "prev",
            "n_infectious_mos",
            "n_total_mos_pop",
            "EIR_gamb",
        ]
        df = pd.read_csv(os.path.join(wdir, "malariasimulation", "All_Age_Outputs.csv"))
        df["date"] = pd.to_datetime(df["date"])
        df["simday"] = (df["date"] - df["date"].min()).dt.days
        scen_df = pd.read_csv(os.path.join(wdir, "scenarios.csv"))
        scen_df = scen_df[["index", "target_output_values"]]
        df = df.merge(scen_df, on="index", how="inner")
        all_age_sample_plot(
            wdir,
            df,
            "malariasimulation",
            timestep_var="simday",
            sweep_variables=exp_tags,
            sample_channels=sample_channels,
        )
