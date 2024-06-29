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


# Helps process script inputs
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
    parser.add_argument(
        "-m",
        "--emodom",
        nargs='+',
        type=str,
        required=False,
        help="Name of models to compare",
        default=['EMOD', 'OpenMalaria', 'MalSim']
    )

    return parser.parse_args()


def custom_sort_key(age_group):
    return int(age_group.split('-')[0])


# Creates the combined dataframes for all models simulated.
def get_output_df(wdir, emodom, yr=False, mth=False, daily=False, custom_name=None, condensed=False,
                  save_combined=False):
    """
    Load and combine data from the model output files.
    Parameters:
        wdir (str): Working directory where the data files are located.
        emodom (str or list of str): Name of models for which result CSVs should be loaded, case sensitive.
        mth (bool, optional): Set to True if the data files have monthly data. Default is False.
        daily (bool, optional): Set to True if the data files have daily timestep data. Default is False. If both mth and daily are true, only daily will be processed.
        timeseries (bool, optional): Set to True if the unaggregated timeseries data should be read in. Default is False
        condensed (bool, optional): Set to True, only a set list of eirs will be present in the final csv.
    Returns:
        df (DataFrame): Combined DataFrame containing the combined data for the models listed in emodom.
        wdir (str): Updated working directory (if applicable).
    Raises:
        ValueError: If invalid emodom value is specified.
    """
    cols_to_keep = None  # default read all
    fname = 'Benchmark.csv'
    if yr:
        fname = 'PfPR_ClinicalIncidence_yr.csv'
    if mth:
        fname = 'PfPR_ClinicalIncidence_mth.csv'
    if daily:
        fname = 'PfPR_ClinicalIncidence_daily.csv'
        # cols_to_keep = ['index', 'timestep', 'ageGroup', 'simulatedEIR', 'prevalence_2to10', 'prevalence',
        #                'clinical_incidence', 'severe_incidence', 'seed']
    if custom_name:
        fname = f'{custom_name}.csv'

    if os.path.isfile(os.path.join(wdir, fname)):
        df = pd.read_csv((os.path.join(wdir, fname)), low_memory=False)
    else:
        if len(emodom) == 1:
            if 'OpenMalaria' in emodom:
                df = pd.read_csv((os.path.join(wdir, f'om/{fname}')), usecols=cols_to_keep)
                df['emodom'] = 'OpenMalaria'
            elif 'EMOD' in emodom:
                df = pd.read_csv((os.path.join(wdir, f'em/{fname}')), usecols=cols_to_keep)
                df['emodom'] = 'EMOD'
            elif 'MalSim' in emodom:
                df = pd.read_csv((os.path.join(wdir, f'MalSim/{fname}')), usecols=cols_to_keep)
                df['emodom'] = 'MalSim'
            else:
                raise ValueError(
                    f"Please specify emodom as some combination of EMOD, OpenMalaria, and MalSim (list), {emodom} not valid")
        else:
            if 'OpenMalaria' in emodom:
                om_df = pd.read_csv((os.path.join(wdir, f'om/{fname}')), usecols=cols_to_keep)
                om_df['emodom'] = 'OpenMalaria'

            if 'EMOD' in emodom:
                em_df = pd.read_csv((os.path.join(wdir, f'em/{fname}')), usecols=cols_to_keep)
                em_df['emodom'] = 'EMOD'
                em_df['seed'] = em_df[
                                    'seed'] + 1  # increase the seed count by one to make sure seed number is consistent across models
                # em_df = em_df[em_df['eir'] >= 1]  # get rid of eirs <1 as EMOD can't sustain malaria at an eir less than 1, for pop of 10,000.

            if 'MalSim' in emodom:
                ms_df = pd.read_csv((os.path.join(wdir, f'MalSim/{fname}')), usecols=cols_to_keep)
                ms_df['emodom'] = 'MalSim'

            if 'EMOD' in emodom and 'OpenMalaria' in emodom and 'MalSim' in emodom:
                df = pd.concat([em_df, om_df])
                df = pd.concat([df, ms_df])
            elif 'OpenMalaria' in emodom and 'EMOD' in emodom and 'MalSim' not in emodom:
                df = pd.concat([em_df, om_df])
            elif 'OpenMalaria' in emodom and 'MalSim' in emodom and 'EMOD' not in emodom:
                df = pd.concat([ms_df, om_df])
            elif 'EMOD' in emodom and 'MalSim' in emodom and 'OpenMalaria' not in emodom:
                df = pd.concat([em_df, ms_df])
            else:
                raise ValueError(
                    f"Please specify emodom as some combination of EMOD, OpenMalaria, and MalSim (list), {emodom} not valid")

        if 'ageGroup' in df.columns:
            try:
                age_grps = sorted(list(df['ageGroup'].unique()), key=custom_sort_key)
            except:
                age_grps = list(df['ageGroup'].unique())
            df['ageGroup'] = df['ageGroup'].astype('category')
            df['ageGroup'] = df['ageGroup'].cat.reorder_categories(age_grps)

        if condensed:  # For our testing purposes, we can reduce the eir's in our simulations to the 6 we think are most useful to compare/graph together.
            eir_list = [1, 5, 10, 50, 200, 1000]
            df = df[df['eir'].isin(eir_list)]
        warning_df = df[df['simulatedEIR'] == 0]

        if len(warning_df) > 0 and daily is False:  # we don't want to include simulations were eir was 0 or less, because we won't get any outcome measures and that crashes the system
            print('Warning: some eirs had simulated EIRS of 0, and were removed')
            df = df[df['simulatedEIR'] > 0]
            df = df[df['simulatedEIR'].notnull()]

        if not daily and save_combined:
            df.to_csv(os.path.join(wdir, f'{fname}'), index=False)
    return df, wdir


# Calculates x-axis and y-axis values for each plot
def get_x_y(df, grpvar, x_channel, y_channel):
    """
    Load and combine data from the model output files.
    Parameters:
        df (DataFrame): The Dataframe we will use to group and calculate our x and y values.
        grpvar (str): The variable in the dataframe we will group the x and y values by.
        x_channel (str): The variable that will serve as our x axis in the graph
        y_channel (str): The variable that will serve as our y axis in the graph
    Returns:
        xmean (DataFrame): a DataFrame containing values for the x axis.
        ymean (DataFrame): a DataFrame containing values for the y axis as well as either 95% confidence interval or percentiles 2.75 to 97.25
    """
    xmean = df.groupby(grpvar)[x_channel].agg(np.mean).reset_index()
    ymean = df.groupby(grpvar)[y_channel].agg(np.mean).reset_index()
    p_df = pd.DataFrame(columns=[grpvar, f'{y_channel}_min', f'{y_channel}_max'])
    for i, row in ymean.iterrows():
        p = df[df[grpvar] == row[grpvar]]
        pmin = np.nanpercentile(p[y_channel], 2.5, axis=0)
        pmax = np.nanpercentile(p[y_channel], 97.5, axis=0)
        new_row = pd.DataFrame([{grpvar: row[grpvar], f'{y_channel}_min': pmin, f'{y_channel}_max': pmax}])
        p_df = pd.concat([p_df, new_row], axis=0, ignore_index=True)
    ymean = pd.merge(left=ymean, right=p_df, on=grpvar)
    return xmean, ymean


def convert_to_date(x):
    import datetime
    return datetime.date(2005, 1, 1) + datetime.timedelta(days=x)


def color_selector(i, s):
    if s == 'EMOD':
        return 0
    elif s == 'MalSim':
        return 1
    elif s == 'OpenMalaria':
        return 2
    else:
        return i
